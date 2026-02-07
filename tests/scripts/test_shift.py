"""Tests for :mod:`scripts.shift` script.

Includes an example-based test for shifting opening balances and a
property-based test for numeric shifts.
"""

from os import PathLike
from unittest.mock import patch

import pytest
from anyio import Path, TemporaryDirectory
from hypothesis import given
from hypothesis import strategies as st

from scripts import shift


@pytest.mark.asyncio
async def test_shift_adjusts_balance(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Shift should modify opening balances in the monthly journal by amount."""
    ledger = Path(tmp_path) / "ledger"
    await (ledger / "2024-01").mkdir(parents=True)
    j = ledger / "2024-01" / "self.journal"
    await j.write_text(
        "2024-01-01 * opening balances\n    assets:bank  1,000.00 HKD = 1,000.00 HKD\n"
    )

    monkeypatch.setattr(shift, "get_ledger_folder", lambda: ledger)

    args = shift.Arguments(
        from_datetime=None,
        to_datetime=None,
        account="assets:bank",
        amount=100.0,
        currency="HKD",
    )
    # Accept the SystemExit raised by exit(0)
    with pytest.raises(SystemExit) as exc:
        await shift.main(args)
    assert exc.value.code == 0

    contents = await j.read_text()
    # after shifting opening balances by +100, the left side becomes 1100.00
    assert "1,100.00 HKD" in contents or "1100.00 HKD" in contents


@pytest.mark.asyncio
@given(
    base=st.integers(min_value=0, max_value=10000),
    shift_amt=st.floats(min_value=-500, max_value=500),
)
async def test_shift_property_adjusts_amounts(base: int, shift_amt: float) -> None:
    """Property-based async test: shifting by an integer amount yields expected result."""
    shift_amt = float(shift_amt)

    async with TemporaryDirectory() as tmpdir:
        ledger = Path(tmpdir) / "ledger"
        await (ledger / "2024-01").mkdir(parents=True)
        j = ledger / "2024-01" / "self.journal"
        await j.write_text(
            f"2024-01-01 * opening balances\n    assets:bank  {base:.2f} HKD = {base:.2f} HKD\n"
        )

        with patch.object(shift, "get_ledger_folder", lambda: ledger):
            args = shift.Arguments(
                from_datetime=None,
                to_datetime=None,
                account="assets:bank",
                amount=shift_amt,
                currency="HKD",
            )
            with pytest.raises(SystemExit):
                await shift.main(args)

        contents = await j.read_text()
        # Expect left amount to equal base + shift_amt
        expected = round(base + shift_amt, 2)
        expected_str = f"{expected:,.2f} HKD"
        assert expected_str in contents or f"{expected:.2f} HKD" in contents


def test_shift_parser_parses_flags() -> None:
    """Parser parses the -f flag and exposes a `from`/`from_` attribute for the start period."""
    p = shift.parser()
    ns = p.parse_args(["-f", "2024-01", "assets:bank", "100", "HKD"])
    assert hasattr(ns, "from") or hasattr(ns, "from_")
