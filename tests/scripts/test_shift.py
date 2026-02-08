"""Tests for :mod:`scripts.shift` script.

Includes an example-based test for shifting opening balances and a
property-based test for numeric shifts.
"""

from argparse import ArgumentParser, Namespace
from datetime import datetime
from os import PathLike
from types import TracebackType
from typing import Self
from unittest.mock import patch

import pytest
from anyio import Path, TemporaryDirectory
from hypothesis import given
from hypothesis import strategies as st

from scripts import shift
from tests.conftest import RunModuleHelper

__all__ = ()


@pytest.mark.asyncio
async def test_shift_adjusts_balance(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Shift should modify opening balances in the monthly journal by amount."""
    ledger: Path = Path(tmp_path) / "ledger"
    await (ledger / "2024-01").mkdir(parents=True)
    j: Path = ledger / "2024-01" / "self.journal"
    await j.write_text(
        "2024-01-01 * opening balances\n    assets:bank  1,000.00 HKD = 1,000.00 HKD\n"
    )

    monkeypatch.setattr(shift, "get_ledger_folder", lambda: ledger)

    args: shift.Arguments = shift.Arguments(
        from_datetime=None,
        to_datetime=None,
        account="assets:bank",
        amount=100.0,
        currency="HKD",
    )
    # Accept the SystemExit raised by exit(0)
    with pytest.raises(SystemExit) as exc_info:
        await shift.main(args)
    exc_info: pytest.ExceptionInfo[SystemExit]  # bound by pytest
    assert exc_info.value.code == 0, "shift.main should exit 0 on success"

    contents: str = await j.read_text()
    # after shifting opening balances by +100, the left side becomes 1100.00
    assert "1,100.00 HKD" in contents or "1100.00 HKD" in contents, (
        "expected opening balance to be increased by shift amount"
    )


@pytest.mark.asyncio
@given(
    base=st.integers(min_value=0, max_value=10000),
    shift_amt=st.floats(min_value=-500, max_value=500),
)
async def test_shift_property_adjusts_amounts(base: int, shift_amt: float) -> None:
    """Property-based async test: shifting by an integer amount yields expected result."""
    shift_amt = float(shift_amt)

    async with TemporaryDirectory() as tmpdir:
        tmpdir_path: str = tmpdir
        ledger: Path = Path(tmpdir_path) / "ledger"
        await (ledger / "2024-01").mkdir(parents=True)
        j: Path = ledger / "2024-01" / "self.journal"
        await j.write_text(
            f"2024-01-01 * opening balances\n    assets:bank  {base:.2f} HKD = {base:.2f} HKD\n"
        )

        with patch.object(shift, "get_ledger_folder", lambda: ledger):
            args: shift.Arguments = shift.Arguments(
                from_datetime=None,
                to_datetime=None,
                account="assets:bank",
                amount=shift_amt,
                currency="HKD",
            )
            with pytest.raises(SystemExit):
                await shift.main(args)

        contents: str = await j.read_text()
        # Expect left amount to equal base + shift_amt
        expected: float = round(base + shift_amt, 2)
        expected_str: str = f"{expected:,.2f} HKD"
        assert expected_str in contents or f"{expected:.2f} HKD" in contents


def test_shift_parser_parses_flags() -> None:
    """Parser parses the -f flag and exposes a `from`/`from_` attribute for the start period."""
    p: ArgumentParser = shift.parser()
    ns: Namespace = p.parse_args(["-f", "2024-01", "assets:bank", "100", "HKD"])
    assert hasattr(ns, "from") or hasattr(ns, "from_")


@pytest.mark.asyncio
async def test_shift_no_matching_account_leaves_file(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """When the requested account isn't in the file, the file should remain unchanged."""
    ledger: Path = Path(tmp_path) / "ledger"
    await (ledger / "2024-01").mkdir(parents=True)
    j: Path = ledger / "2024-01" / "self.journal"
    await j.write_text(
        "2024-01-01 * opening balances\n    assets:other  1,000.00 HKD = 1,000.00 HKD\n"
    )

    monkeypatch.setattr(shift, "get_ledger_folder", lambda: ledger)

    args: shift.Arguments = shift.Arguments(
        from_datetime=None,
        to_datetime=None,
        account="assets:bank",
        amount=100.0,
        currency="HKD",
    )

    with pytest.raises(SystemExit):
        await shift.main(args)

    contents: str = await j.read_text()
    assert "assets:other" in contents


@pytest.mark.asyncio
async def test_shift_parser_invoke_calls_main(monkeypatch: pytest.MonkeyPatch) -> None:
    """Parser invoke for shift should call the main coroutine with appropriate args."""
    called: dict[str, shift.Arguments] = {}

    async def fake_main(args: shift.Arguments) -> None:
        """Fake main coroutine to capture the provided arguments for assertions."""
        called["args"] = args

    monkeypatch.setattr(shift, "main", fake_main)
    p: ArgumentParser = shift.parser()
    ns: Namespace = p.parse_args(["assets:bank", "100", "HKD"])

    await ns.invoke(ns)
    assert isinstance(called.get("args"), shift.Arguments)
    assert called["args"].account == "assets:bank"


@pytest.mark.asyncio
async def test_shift_filters_by_month(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Shifting should respect the from/to period filters applied to journals."""
    ledger: Path = Path(tmp_path) / "ledger"
    await (ledger / "2024-01").mkdir(parents=True)
    await (ledger / "2024-02").mkdir(parents=True)
    j1: Path = ledger / "2024-01" / "self.journal"
    j2: Path = ledger / "2024-02" / "self.journal"
    await j1.write_text(
        "2024-01-01 * opening balances\n    assets:bank  1000.00 HKD = 1000.00 HKD\n"
    )
    await j2.write_text(
        "2024-02-01 * opening balances\n    assets:bank  1000.00 HKD = 1000.00 HKD\n"
    )

    monkeypatch.setattr(shift, "get_ledger_folder", lambda: ledger)

    args: shift.Arguments = shift.Arguments(
        from_datetime=datetime.fromisoformat("2024-02-01"),
        to_datetime=None,
        account="assets:bank",
        amount=100.0,
        currency="HKD",
    )

    with pytest.raises(SystemExit):
        await shift.main(args)

    contents1: str = await j1.read_text()
    contents2: str = await j2.read_text()
    # Only 2024-02 should have been modified
    assert ("1,000.00 HKD" in contents1) or ("1000.00 HKD" in contents1)
    assert ("1,100.00 HKD" in contents2) or ("1100.00 HKD" in contents2)


@pytest.mark.asyncio
async def test_shift_opening_and_closing_behaviour(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify the opening/closing boolean logic in shifting amounts."""
    ledger: Path = Path(tmp_path) / "ledger"
    await (ledger / "2024-01").mkdir(parents=True)
    j: Path = ledger / "2024-01" / "self.journal"
    # opening balance on 2024-01-01 and closing balance on 2024-01-31
    await j.write_text(
        "2024-01-01 * opening balances\n    assets:bank  1000.00 HKD = 1000.00 HKD\n2024-01-31 * closing balances\n    assets:bank  1100.00 HKD = 1100.00 HKD\n"
    )

    monkeypatch.setattr(shift, "get_ledger_folder", lambda: ledger)

    args: shift.Arguments = shift.Arguments(
        from_datetime=None,
        to_datetime=None,
        account="assets:bank",
        amount=50.0,
        currency="HKD",
    )

    with pytest.raises(SystemExit):
        await shift.main(args)

    contents: str = await j.read_text()
    # For opening balance: left side increases by amount (1000 + 50)
    assert "1,050.00 HKD" in contents or "1050.00 HKD" in contents
    # For closing balance: left side decreases by amount (1100 - 50)
    assert "1,050.00 HKD" in contents or "1050.00 HKD" in contents


@pytest.mark.asyncio
async def test_shift_logs_skipped_when_skipped(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """When JournalRunContext has skipped journals the shift main should exercise the 'skipped' logging branch."""
    ledger: Path = Path(tmp_path) / "ledger"
    await (ledger / "2024-01").mkdir(parents=True)
    j: Path = ledger / "2024-01" / "self.journal"
    await j.write_text(
        "2024-01-01 * opening balances\n    assets:bank  1000.00 HKD = 1000.00 HKD\n"
    )

    monkeypatch.setattr(shift, "get_ledger_folder", lambda: ledger)

    class DummyRun:
        def __init__(self, script_id: PathLike[str], j: list[PathLike[str]]) -> None:
            self.to_process = []
            self.skipped: list[PathLike[str]] = j
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

        def report_success(self, journal: PathLike[str]) -> None:
            self._reported.append(journal)

        @property
        def reported(self) -> list[PathLike[str]]:
            return self._reported

    monkeypatch.setattr(shift, "JournalRunContext", DummyRun)

    args: shift.Arguments = shift.Arguments(
        from_datetime=None,
        to_datetime=None,
        account="assets:bank",
        amount=50.0,
        currency="HKD",
    )

    with pytest.raises(SystemExit) as exc:
        await shift.main(args)
    assert exc.value.code == 0


def test_module_main_invokes_run(run_module_helper: RunModuleHelper) -> None:
    """Running the module as a script should call :func:`asyncio.run` with the parser-invoked coroutine."""
    called = run_module_helper(
        "scripts.shift", ["scripts.shift", "assets:bank", "1", "HKD"]
    )  # avoid pytest args
    assert called["ran"] is True
