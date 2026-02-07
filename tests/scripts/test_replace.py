"""Tests for :mod:`scripts.replace` script.

Covers file discovery and basic replacement semantics.
"""

from os import PathLike

import pytest
from anyio import Path

from scripts import replace


@pytest.mark.asyncio
async def test_replace_rewrites_files(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Running the replace script should rewrite matching files under the ledger."""
    ledger = Path(tmp_path) / "ledger"
    await ledger.mkdir()
    j1 = ledger / "2024-01" / "self.journal"
    await j1.parent.mkdir()
    await j1.write_text("payee: OLD\n")

    monkeypatch.setattr(replace, "get_ledger_folder", lambda: ledger)

    args = replace.Arguments(find="OLD", replace="NEW")
    # Accept the SystemExit raised by exit(0)
    with pytest.raises(SystemExit) as exc:
        await replace.main(args)
    assert exc.value.code == 0

    assert "NEW" in await j1.read_text()


@pytest.mark.asyncio
async def test_replace_property_many_files(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Replacement should apply to all files and not leave the old text behind."""
    # Simple property-style test using fixed variants
    ledger = Path(tmp_path) / "ledger"
    await ledger.mkdir()
    contents = ["alpha OLD beta", "nope", "OLDOLD", "x OLD y"]
    files: list[tuple[Path, str]] = []
    for i, c in enumerate(contents):
        p = ledger / f"2024-0{i+1}" / f"f{i}.journal"
        await p.parent.mkdir(parents=True, exist_ok=True)
        await p.write_text(c)
        files.append((p, c))

    monkeypatch.setattr(replace, "get_ledger_folder", lambda: ledger)

    args = replace.Arguments(find="OLD", replace="NEW")
    with pytest.raises(SystemExit):
        await replace.main(args)

    for p, c in files:
        text = await p.read_text()
        assert "OLD" not in text
        assert c.replace("OLD", "NEW") in text


def test_replace_parser_requires_args() -> None:
    """Parser should accept positional find/replace arguments."""
    p = replace.parser()
    ns = p.parse_args(["findtext", "repltext"])
    assert ns.find == "findtext"
    assert ns.replace == "repltext"
