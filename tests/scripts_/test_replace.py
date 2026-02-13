"""Tests for :mod:`scripts.replace` script.

Covers file discovery and basic replacement semantics.
"""

from os import PathLike

import pytest
from anyio import Path

from scripts import replace
from tests.conftest import RunModuleHelper

__all__ = ()


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
    assert exc.value.code == 0, "replace.main should exit 0 on success"

    assert "NEW" in await j1.read_text(), (
        "replacement should change file contents to include NEW"
    )


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
        p = ledger / f"2024-0{i + 1}" / f"f{i}.journal"
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


@pytest.mark.asyncio
async def test_replace_with_no_journals(monkeypatch: pytest.MonkeyPatch) -> None:
    """When no journals are discovered, replace should complete without error."""

    async def fake_find(folder: PathLike[str]) -> list[PathLike[str]]:
        return []

    monkeypatch.setattr(replace, "find_all_journals", fake_find)
    args = replace.Arguments(find="X", replace="Y")
    # completes normally
    with pytest.raises(SystemExit):
        await replace.main(args)


@pytest.mark.asyncio
async def test_replace_parser_invoke_calls_main(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The parser invoke wrapper should call :func:`replace.main` with parsed arguments."""
    called: dict[str, replace.Arguments] = {}

    async def fake_main(args: replace.Arguments) -> None:
        called["args"] = args

    monkeypatch.setattr(replace, "main", fake_main)
    p = replace.parser()
    ns = p.parse_args(["a", "b"])

    await ns.invoke(ns)
    assert isinstance(called.get("args"), replace.Arguments)
    assert called["args"].find == "a" and called["args"].replace == "b"


def test_replace_parser_requires_args() -> None:
    """Parser should accept positional find/replace arguments."""
    p = replace.parser()
    ns = p.parse_args(["findtext", "repltext"])
    assert ns.find == "findtext"
    assert ns.replace == "repltext"


@pytest.mark.asyncio
async def test_replace_noop_leaves_files_unchanged(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """When the find text is not present files should be left unchanged."""
    ledger = Path(tmp_path) / "ledger"
    await ledger.mkdir()
    j1 = ledger / "2024-01" / "self.journal"
    await j1.parent.mkdir()
    await j1.write_text("no matches here\n")

    monkeypatch.setattr(replace, "get_ledger_folder", lambda: ledger)

    before = await j1.read_text()
    args = replace.Arguments(find="NOTTHERE", replace="NEW")
    with pytest.raises(SystemExit):
        await replace.main(args)

    after = await j1.read_text()
    assert before == after


def test_module_main_invokes_run(run_module_helper: RunModuleHelper) -> None:
    """Running the module as a script should call :func:`asyncio.run` with the parser-invoked coroutine."""
    called = run_module_helper(
        "scripts.replace", ["scripts.replace", "a", "b"]
    )  # avoid pytest args
    assert called["ran"] is True
