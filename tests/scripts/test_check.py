"""Tests for :mod:`scripts.check`.

Ensure the CLI parser exposes the expected invocation hooks.
"""

from collections.abc import Iterable
from os import PathLike
from types import TracebackType

import pytest
from anyio import Path

from scripts import check


def test_check_parser_invoke_callable() -> None:
    """Parser should attach an 'invoke' callable for the subcommand."""
    p = check.parser()
    ns = p.parse_args([])
    assert hasattr(ns, "invoke")


@pytest.mark.asyncio
async def test_check_main_runs_hledger_for_each_journal(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
):
    """Main should invoke `run_hledger` for each journal that requires processing.

    This test stubs out the discovery and the JournalRunContext so the
    behaviour of `main` can be observed without touching global cache files.
    """
    # Create a simple ledger with two monthly journals
    repo = Path(tmp_path) / "ledger"
    await (repo / "2024-01").mkdir(parents=True)
    await (repo / "2024-01" / "a.journal").write_text("x")
    await (repo / "2024-02").mkdir(parents=True)
    await (repo / "2024-02" / "b.journal").write_text("y")

    journals: list[PathLike[str]] = [
        repo / "2024-01" / "a.journal",
        repo / "2024-02" / "b.journal",
    ]

    # Point ledger discovery at our temporary repo
    monkeypatch.setattr(check, "get_ledger_folder", lambda: repo)

    async def fake_find(
        folder: PathLike[str], files: Iterable[str] | None = None
    ) -> list[PathLike[str]]:
        """Fake discovery implementation that returns the local test journals list."""
        return journals

    monkeypatch.setattr(check, "find_monthly_journals", fake_find)

    calls: list[PathLike[str]] = []

    async def fake_run_hledger(
        journal: PathLike[str], *args: object
    ) -> tuple[str, str, int]:
        """Fake hledger runner used by tests to capture invocation without subprocesses."""
        calls.append(journal)
        return ("", "", 0)

    monkeypatch.setattr(check, "run_hledger", fake_run_hledger)

    # Stub JournalRunContext so everything is treated as 'to_process'
    class DummyRun:
        """A minimal JournalRunContext stub used by tests to emulate session behaviour."""

        def __init__(self, script_id: PathLike[str], j: list[PathLike[str]]) -> None:
            """Initialize with a list of journals to process and empty reported/skipped lists."""
            self.to_process = list(j)
            self.skipped: list[PathLike[str]] = []
            self._reported: list[PathLike[str]] = []

        async def __aenter__(self) -> "DummyRun":
            """Async context manager entry: return self for use in tests."""
            return self

        async def __aexit__(
            self,
            exc_type: type | None,
            exc: BaseException | None,
            tb: TracebackType | None,
        ) -> bool:
            """Async context manager exit: no cleanup required in tests."""
            return False

        def report_success(self, journal: PathLike[str]) -> None:
            """Record a successful journal processing for assertions in tests."""
            self._reported.append(journal)

        @property
        def reported(self) -> list[PathLike[str]]:
            """Return the list of reported journals for test assertions."""
            return self._reported

    monkeypatch.setattr(check, "JournalRunContext", DummyRun)

    args = check.Arguments(files=None)

    with pytest.raises(SystemExit) as exc:
        await check.main(args)
    assert exc.value.code == 0
    # ensure run_hledger was called for both journals
    assert len(calls) == 2
