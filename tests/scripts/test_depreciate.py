"""Tests for :mod:`scripts.depreciate`.

Validate that depreciation transactions are appended and parser arguments are
interpreted correctly.
"""

from os import PathLike

import pytest
from anyio import Path

from scripts import depreciate


@pytest.mark.asyncio
async def test_depreciate_appends_transaction(
    tmp_path: PathLike, monkeypatch: pytest.MonkeyPatch
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
