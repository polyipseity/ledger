"""Tests for :mod:`scripts.depreciate`.

Validate that depreciation transactions are appended and parser arguments are
interpreted correctly.
"""

from os import PathLike
from types import TracebackType
from typing import Self

import pytest
from anyio import Path

from scripts import depreciate
from tests.conftest import RunModuleHelper

__all__ = ()


@pytest.mark.asyncio
async def test_depreciate_appends_transaction(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Depreciate appends a transaction to the journal and writes amounts."""
    ledger = Path(tmp_path) / "ledger"
    await (ledger / "2024-01").mkdir(parents=True)
    j = ledger / "2024-01" / "self.journal"
    await j.write_text("2024-01-01 * opening balances\n")

    monkeypatch.setattr(depreciate, "get_ledger_folder", lambda: ledger)

    args = depreciate.Arguments(
        from_datetime=None,
        to_datetime=None,
        item="widget",
        amount=12.34,
        currency="HKD",
    )
    # script calls `exit(0)` on success which raises SystemExit; accept that
    with pytest.raises(SystemExit) as exc:
        await depreciate.main(args)
    assert exc.value.code == 0

    # the file should have been updated before the exit
    contents = await j.read_text()
    assert "accumulated depreciation" in contents
    assert "widget" in contents
    assert "12.34" in contents


def test_depreciate_parser_parses() -> None:
    """CLI parser extracts item, amount and currency correctly."""
    p = depreciate.parser()
    ns = p.parse_args(["widget", "12.34", "HKD"])
    assert ns.item == "widget"
    assert float(ns.amount) == 12.34
    assert ns.currency == "HKD"


def test_depreciate_parser_with_from_to_flags() -> None:
    """Parser should accept -f and -t period flags and parse them into datetimes."""
    p = depreciate.parser()
    ns = p.parse_args(["-f", "2024-01", "-t", "2024-03", "widget", "1", "HKD"])
    # parser now sets 'from_' dest to avoid using the reserved keyword; ensure both exist
    assert getattr(ns, "from_") is not None, (
        "expected parser to set 'from_' start period"
    )
    assert getattr(ns, "to") is not None, "expected parser to set 'to' end period"


@pytest.mark.asyncio
async def test_depreciate_main_logs_skipped_when_skipped(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """When JournalRunContext has skipped journals, main should exercise the 'skipped' logging branch."""
    repo = Path(tmp_path) / "ledger"
    await (repo / "2024-01").mkdir(parents=True)
    await (repo / "2024-01" / "a.journal").write_text("x")

    async def fake_find(
        folder: PathLike[str], files: object = None
    ) -> list[PathLike[str]]:
        return [repo / "2024-01" / "a.journal"]

    monkeypatch.setattr(depreciate, "find_monthly_journals", fake_find)

    class DummyRun:
        def __init__(self, script_id: PathLike[str], j: list[PathLike[str]]) -> None:
            self.to_process = []
            self.skipped: list[PathLike[str]] = [repo / "2024-01" / "a.journal"]
            self._reported: list[PathLike[str]] = []

        async def __aenter__(self) -> Self:
            return self

        async def __aexit__(
            self,
            exc_type: type | None,
            exc: BaseException | None,
            tb: TracebackType | None,
        ) -> bool:
            return False

        def report_success(
            self, journal: PathLike[str]
        ) -> None:  # pragma: no cover - trivial
            self._reported.append(journal)

        @property
        def reported(self) -> list[PathLike[str]]:  # pragma: no cover - trivial
            return self._reported

    monkeypatch.setattr(depreciate, "JournalRunContext", DummyRun)

    # Should complete cleanly
    with pytest.raises(SystemExit) as exc:
        await depreciate.main(
            depreciate.Arguments(
                from_datetime=None,
                to_datetime=None,
                item="x",
                amount=1.0,
                currency="HKD",
            )
        )
    assert exc.value.code == 0


@pytest.mark.asyncio
async def test_depreciate_parser_invoke_calls_main(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The parser invoke wrapper should call :func:`depreciate.main` with parsed args."""
    called: dict[str, object] = {}

    async def fake_main(args: depreciate.Arguments) -> None:
        called["args"] = args

    monkeypatch.setattr(depreciate, "main", fake_main)
    p = depreciate.parser()
    ns = p.parse_args(["widget", "1", "HKD"])

    await ns.invoke(ns)
    assert isinstance(called.get("args"), depreciate.Arguments)


def test_module_main_invokes_run(run_module_helper: RunModuleHelper) -> None:
    """Running the module as a script should call :func:`asyncio.run` with the parser-invoked coroutine."""
    called = run_module_helper(
        "scripts.depreciate", ["scripts.depreciate", "x", "1", "HKD"]
    )  # avoid pytest args
    assert called["ran"] is True


@pytest.mark.asyncio
async def test_depreciate_inserts_accumulated_when_depreciation_present_with_blank(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """When a depreciation txn exists that is followed by a blank line, the accumulated posting is inserted before the blank line."""
    ledger = Path(tmp_path) / "ledger"
    await (ledger / "2024-01").mkdir(parents=True)
    j = ledger / "2024-01" / "self.journal"
    # create a depreciation transaction that ends with a blank line
    await j.write_text(
        "2024-01-31 ! depreciation  ; activity: depreciation, time: 23:59:59, timezone: UTC+08:00\n    expenses:depreciation\n\n"
    )

    monkeypatch.setattr(depreciate, "get_ledger_folder", lambda: ledger)

    args = depreciate.Arguments(
        from_datetime=None,
        to_datetime=None,
        item="widget",
        amount=7.5,
        currency="HKD",
    )

    with pytest.raises(SystemExit):
        await depreciate.main(args)

    contents = await j.read_text()
    assert "assets:accumulated depreciation" in contents
    assert "item: widget" in contents


@pytest.mark.asyncio
async def test_depreciate_appends_when_no_trailing_blank(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """If a depreciation txn exists with no trailing blank line, the accumulated posting is appended to the file."""
    ledger = Path(tmp_path) / "ledger"
    await (ledger / "2024-01").mkdir(parents=True)
    j = ledger / "2024-01" / "self.journal"
    # create a depreciation transaction that is at EOF (no blank line)
    await j.write_text(
        "2024-01-31 ! depreciation  ; activity: depreciation, time: 23:59:59, timezone: UTC+08:00\n    expenses:depreciation\n"
    )

    monkeypatch.setattr(depreciate, "get_ledger_folder", lambda: ledger)

    args = depreciate.Arguments(
        from_datetime=None,
        to_datetime=None,
        item="gadget",
        amount=1.0,
        currency="HKD",
    )

    with pytest.raises(SystemExit):
        await depreciate.main(args)

    contents = await j.read_text()
    # appended block should include accumulated depreciation near the end
    assert (
        contents.strip().endswith("item: gadget")
        or "assets:accumulated depreciation" in contents
    )
