"""Tests for the :mod:`scripts.clopen` helper.

These exercises cover the happy path and the various failure modes described in
its documentation.  The test style mirrors the existing suite of script tests
so that reviewers will find the patterns familiar.
"""

from argparse import ArgumentParser, Namespace
from os import PathLike

import pytest
from anyio import Path

from scripts import clopen

from ..utils import RunModuleHelper

"""Public symbols exported by this module (none)."""
__all__ = ()


# sample output from `hledger ... --clopen` for an example journal; tags/time added
"""Example closing-balance transaction string for assertions."""
CLOSING_TX = (
    "2026-02-28 closing balances  ; clopen:, time: 23:59:59, timezone: UTC+08:00\n"
    "    assets:bank  100.00 HKD = 100.00 HKD"
)
"""Example opening-balance transaction string for assertions."""
OPENING_TX = (
    "2026-03-01 opening balances  ; clopen:, time: 00:00:00, timezone: UTC+08:00\n"
    "    assets:bank  100.00 HKD = 100.00 HKD"
)


@pytest.mark.anyio
async def test_clopen_happy_path(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The script should append a closing entry and prepend an opening entry."""

    ledger: Path = Path(tmp_path) / "ledger"
    # create February and March folders for both normal and alternatives
    # layout styles.  the script should work regardless of whether a year
    # subdirectory is present or not.
    await (ledger / "2026-02").mkdir(parents=True)
    await (ledger / "2026-03").mkdir(parents=True)
    # also create a nested year folder layout to ensure both are handled
    await (ledger / "2026" / "2026-02").mkdir(parents=True)
    await (ledger / "2026" / "2026-03").mkdir(parents=True)

    old_j: Path = ledger / "2026-02" / "self.journal"
    new_j: Path = ledger / "2026-03" / "self.journal"
    old_alt: Path = ledger / "2026" / "2026-02" / "self.alternatives.journal"
    new_alt: Path = ledger / "2026" / "2026-03" / "self.alternatives.journal"

    # include lines to verify prepend logic
    for path in (old_j, new_j, old_alt, new_alt):
        await path.write_text('include "preludes/self.journal"\n')

    # stub the ledger folder and the hledger call
    monkeypatch.setattr(clopen, "get_ledger_folder", lambda: ledger)

    async def fake_run_hledger(journal: PathLike[str], *args: object):
        """Return canned closing/opening output for ``journal``."""

        return (f"{CLOSING_TX}\n\n{OPENING_TX}\n", "", 0)

    monkeypatch.setattr(clopen, "run_hledger", fake_run_hledger)

    args = clopen.Arguments(period="2026-02")
    with pytest.raises(SystemExit) as exc:
        await clopen.main(args)
    assert exc.value.code == 0

    contents_old = await old_j.read_text()
    assert "2026-02-28 closing balances" in contents_old
    # closing line should contain tags in alphabetical key order: clopen, time, timezone
    closing_line = [
        line
        for line in contents_old.splitlines()
        if line.strip().startswith("2026-02-28")
    ][0]
    assert "clopen:" in closing_line
    assert "time: 23:59:59" in closing_line
    assert "timezone: UTC+08:00" in closing_line
    # verify ordering
    order = [closing_line.index(x) for x in ["clopen:", "time:", "timezone:"]]
    assert order == sorted(order)
    contents_new = await new_j.read_text()
    assert "2026-03-01 opening balances" in contents_new
    # there should be a blank line between includes and the opening balance
    lines = contents_new.splitlines()
    assert lines[0].startswith("include ")
    assert lines[1] == ""
    assert lines[2].startswith("2026-03-01")
    opening_line = lines[2]
    assert "clopen:" in opening_line
    assert "time: 00:00:00" in opening_line
    assert "timezone: UTC+08:00" in opening_line
    order = [opening_line.index(x) for x in ["clopen:", "time:", "timezone:"]]
    assert order == sorted(order)
    # alternatives journals should also be updated
    contents_old_alt = await old_alt.read_text()
    assert "2026-02-28 closing balances" in contents_old_alt
    contents_new_alt = await new_alt.read_text()
    assert "2026-03-01 opening balances" in contents_new_alt
    # ensure tags on alt opening too
    alt_open_line = [
        line
        for line in contents_new_alt.splitlines()
        if line.strip().startswith("2026-03-01")
    ][0]
    assert "clopen:" in alt_open_line
    assert "time: 00:00:00" in alt_open_line
    assert "timezone: UTC+08:00" in alt_open_line


@pytest.mark.anyio
async def test_clopen_existing_closing_errors(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """If the old journal already contains the closing line the script fails."""

    ledger: Path = Path(tmp_path) / "ledger"
    await (ledger / "2026-02").mkdir(parents=True)
    await (ledger / "2026-03").mkdir(parents=True)
    old_j: Path = ledger / "2026-02" / "self.journal"
    new_j: Path = ledger / "2026-03" / "self.journal"

    await old_j.write_text(CLOSING_TX + "\n")
    await new_j.write_text(OPENING_TX + "\n")

    monkeypatch.setattr(clopen, "get_ledger_folder", lambda: ledger)

    async def fake_run_hledger(journal: PathLike[str], *args: object):
        """Return canned closing/opening output for ``journal``."""

        return (f"{CLOSING_TX}\n\n{OPENING_TX}\n", "", 0)

    monkeypatch.setattr(clopen, "run_hledger", fake_run_hledger)

    args = clopen.Arguments(period="2026-02")
    with pytest.raises(SystemExit) as exc:
        await clopen.main(args)
    assert exc.value.code == 1


@pytest.mark.anyio
async def test_clopen_existing_opening_errors(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """If the new journal already contains the opening line the script fails."""

    ledger: Path = Path(tmp_path) / "ledger"
    await (ledger / "2026-02").mkdir(parents=True)
    await (ledger / "2026-03").mkdir(parents=True)
    old_j: Path = ledger / "2026-02" / "self.journal"
    new_j: Path = ledger / "2026-03" / "self.journal"

    # put closing only in old
    await old_j.write_text("some content\n")
    await new_j.write_text(OPENING_TX + "\n")

    monkeypatch.setattr(clopen, "get_ledger_folder", lambda: ledger)

    async def fake_run_hledger(journal: PathLike[str], *args: object):
        """Return canned closing/opening output for ``journal``."""

        return (f"{CLOSING_TX}\n\n{OPENING_TX}\n", "", 0)

    monkeypatch.setattr(clopen, "run_hledger", fake_run_hledger)

    args = clopen.Arguments(period="2026-02")
    with pytest.raises(SystemExit) as exc:
        await clopen.main(args)
    assert exc.value.code == 1


@pytest.mark.anyio
async def test_clopen_missing_next_journal_appends_closing(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """When the next-month file is missing, only the closing entry is written.
    The script should exit with code 0 (non-fatal) and not prepend opening.
    """

    ledger: Path = Path(tmp_path) / "ledger"
    await (ledger / "2026-02").mkdir(parents=True)
    old_j: Path = ledger / "2026-02" / "self.journal"
    # include line should be copied into new journal
    await old_j.write_text('include "preludes/self.journal"\n')

    monkeypatch.setattr(clopen, "get_ledger_folder", lambda: ledger)

    async def fake_run_hledger(journal: PathLike[str], *args: object):
        """Return canned closing/opening output for ``journal``."""

        return (f"{CLOSING_TX}\n\n{OPENING_TX}\n", "", 0)

    monkeypatch.setattr(clopen, "run_hledger", fake_run_hledger)

    args = clopen.Arguments(period="2026-02")
    with pytest.raises(SystemExit) as exc:
        await clopen.main(args)
    assert exc.value.code == 0

    text = await old_j.read_text()
    assert "2026-02-28 closing balances" in text
    # closing tag checks
    closing_line = [
        line for line in text.splitlines() if line.strip().startswith("2026-02-28")
    ][0]
    assert "time: 23:59:59" in closing_line
    assert "timezone: UTC+08:00" in closing_line
    assert "clopen:" in closing_line

    # new journal should exist and contain the include plus blank line and opening
    new_j = ledger / "2026-03" / "self.journal"
    assert await new_j.exists()
    new_text = await new_j.read_text()
    assert new_text.startswith('include "preludes/self.journal"\n\n')
    assert "2026-03-01 opening balances" in new_text


@pytest.mark.anyio
async def test_clopen_alt_missing_next_still_processes_main(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """When the alternatives journal has no next-month file, both journals
    should still receive their closing entries and the script exits 0.
    """

    ledger: Path = Path(tmp_path) / "ledger"
    # create main directory structure and next-month directory but no files
    await (ledger / "2026" / "2026-02").mkdir(parents=True)
    await (ledger / "2026" / "2026-03").mkdir(parents=True)
    # include lines ensure the new journals will also contain them
    await (ledger / "2026" / "2026-02" / "self.alternatives.journal").write_text(
        'include "preludes/self.alternatives.journal"\n'
    )
    await (ledger / "2026" / "2026-02" / "self.journal").write_text(
        'include "preludes/self.journal"\n'
    )

    monkeypatch.setattr(clopen, "get_ledger_folder", lambda: ledger)

    async def fake_run_hledger(journal: PathLike[str], *args: object):
        """Return canned closing/opening output for ``journal``."""

        return (f"{CLOSING_TX}\n\n{OPENING_TX}\n", "", 0)

    monkeypatch.setattr(clopen, "run_hledger", fake_run_hledger)

    args = clopen.Arguments(period="2026-02")
    with pytest.raises(SystemExit) as exc:
        await clopen.main(args)
    assert exc.value.code == 0

    # both journals should have closing entries
    alt_text = await (
        ledger / "2026" / "2026-02" / "self.alternatives.journal"
    ).read_text()
    assert "2026-02-28 closing balances" in alt_text
    closing_line_alt = [
        line for line in alt_text.splitlines() if line.strip().startswith("2026-02-28")
    ][0]
    assert "time: 23:59:59" in closing_line_alt
    assert "timezone: UTC+08:00" in closing_line_alt
    assert "clopen:" in closing_line_alt
    main_text = await (ledger / "2026" / "2026-02" / "self.journal").read_text()
    assert "2026-02-28 closing balances" in main_text
    closing_line_main = [
        line for line in main_text.splitlines() if line.strip().startswith("2026-02-28")
    ][0]
    assert "time: 23:59:59" in closing_line_main
    assert "timezone: UTC+08:00" in closing_line_main
    assert "clopen:" in closing_line_main

    # and both next-month journals should have been created with include + blank line + opening
    next_alt = ledger / "2026" / "2026-03" / "self.alternatives.journal"
    assert await next_alt.exists()
    next_alt_text = await next_alt.read_text()
    assert next_alt_text.startswith('include "preludes/self.alternatives.journal"\n\n')
    assert "2026-03-01 opening balances" in next_alt_text
    # check tags on created opening
    open_line_alt = [
        line
        for line in next_alt_text.splitlines()
        if line.strip().startswith("2026-03-01")
    ][0]
    assert "time: 00:00:00" in open_line_alt
    assert "timezone: UTC+08:00" in open_line_alt
    assert "clopen:" in open_line_alt

    next_main = ledger / "2026" / "2026-03" / "self.journal"
    assert await next_main.exists()
    next_main_text = await next_main.read_text()
    assert next_main_text.startswith('include "preludes/self.journal"\n\n')
    assert "2026-03-01 opening balances" in next_main_text
    open_line_main = [
        line
        for line in next_main_text.splitlines()
        if line.strip().startswith("2026-03-01")
    ][0]
    assert "time: 00:00:00" in open_line_main
    assert "timezone: UTC+08:00" in open_line_main
    assert "clopen:" in open_line_main


@pytest.mark.anyio
async def test_clopen_no_journals(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Period with no journal files should result in a successful exit (code 0)."""

    ledger: Path = Path(tmp_path) / "ledger"
    # no folders created at all
    monkeypatch.setattr(clopen, "get_ledger_folder", lambda: ledger)

    args = clopen.Arguments(period="2026-02")
    with pytest.raises(SystemExit) as exc:
        await clopen.main(args)
    assert exc.value.code == 0


@pytest.mark.anyio
async def test_clopen_disables_cache(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Clopen should construct JournalRunContext with cache=False."""

    ledger: Path = Path(tmp_path) / "ledger"
    await (ledger / "2026-02").mkdir(parents=True)
    journal = ledger / "2026-02" / "self.journal"
    await journal.write_text('include "preludes/self.journal"\n')

    called: dict[str, bool] = {}

    class DummyCtx:
        """Minimal async context manager stand-in for ``JournalRunContext``."""

        def __init__(
            self,
            script_id: PathLike[str],
            journals: list[PathLike[str]],
            *,
            cache: bool = True,
            **kwargs: object,
        ):
            """Record constructor arguments and store the journals to process."""

            called["cache"] = cache
            self.to_process = list(journals)
            self.skipped: list[PathLike[str]] = []
            self._reported: set[PathLike[str]] = set()

        async def __aenter__(self):
            """Enter the async context and return ``self``."""

            return self

        async def __aexit__(self, *args: object) -> bool:
            """Leave the async context without suppressing exceptions."""

            return False

    monkeypatch.setattr(clopen, "JournalRunContext", DummyCtx)
    monkeypatch.setattr(clopen, "get_ledger_folder", lambda: ledger)

    async def fake_find(
        folder: PathLike[str], files: object = None
    ) -> list[PathLike[str]]:
        """Return a fixed list containing the prepared ``journal`` path."""

        return [journal]

    monkeypatch.setattr(clopen, "find_monthly_journals", fake_find)

    async def fake_run_hledger(
        journal: PathLike[str], *args: object
    ) -> tuple[str, str, int]:
        """Return a tiny dummy closing/opening pair for ``journal``."""

        return ("cl\n\nop", "", 0)

    monkeypatch.setattr(clopen, "run_hledger", fake_run_hledger)

    args = clopen.Arguments(period="2026-02")
    with pytest.raises(SystemExit):
        await clopen.main(args)
    assert called.get("cache") is False


@pytest.mark.anyio
async def test_parser_invokes_main(monkeypatch: pytest.MonkeyPatch) -> None:
    """Parser invoke should call :func:`clopen.main` with the right arguments."""

    called: dict[str, clopen.Arguments] = {}

    async def fake_main(args: clopen.Arguments) -> None:
        """Capture the arguments passed by the parser's ``invoke`` callback."""

        called["args"] = args

    monkeypatch.setattr(clopen, "main", fake_main)
    p: ArgumentParser = clopen.parser()
    ns: Namespace = p.parse_args(["2026-02"])

    # the invoke coroutine returns None
    await ns.invoke(ns)
    assert isinstance(called.get("args"), clopen.Arguments)
    assert called["args"].period == "2026-02"


def test_module_main_invokes_run(run_module_helper: RunModuleHelper) -> None:
    """Running the module as a script should ultimately call ``asyncio.run``.

    This mirrors the tests present for the other helper scripts.
    """

    called = run_module_helper("scripts.clopen", ["scripts.clopen", "2026-02"])
    assert called["ran"] is True
