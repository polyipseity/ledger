"""Tests for the :mod:`scripts.clopen` helper and its boundary verifier.

These exercises cover the happy path and the various failure modes described in
its documentation.  The verifier half writes real journals and drives the real
managed ``hledger`` binary, so those assertions also pin the hledger JSON field
names the module parses.
"""

from argparse import ArgumentParser, Namespace
from calendar import monthrange
from collections.abc import Sequence
from os import PathLike
from pathlib import Path as StdPath

import pytest
from anyio import Path

from scripts import clopen

from ..test_utils import RunModuleHelper

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

    args = clopen.Arguments(command="close", period="2026-02")
    assert await clopen.main(args) == 0

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

    args = clopen.Arguments(command="close", period="2026-02")
    assert await clopen.main(args) == 1


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

    args = clopen.Arguments(command="close", period="2026-02")
    assert await clopen.main(args) == 1


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

    args = clopen.Arguments(command="close", period="2026-02")
    assert await clopen.main(args) == 0

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

    args = clopen.Arguments(command="close", period="2026-02")
    assert await clopen.main(args) == 0

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

    args = clopen.Arguments(command="close", period="2026-02")
    assert await clopen.main(args) == 0


@pytest.mark.anyio
async def test_files_restrict_processed_journals(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """``files`` restricts the run to the named journal of the period."""

    ledger: Path = Path(tmp_path) / "ledger"
    await (ledger / "2026" / "2026-02").mkdir(parents=True)
    await (ledger / "2026" / "2026-03").mkdir(parents=True)

    old_j: Path = ledger / "2026" / "2026-02" / "self.journal"
    new_j: Path = ledger / "2026" / "2026-03" / "self.journal"
    old_alt: Path = ledger / "2026" / "2026-02" / "self.alternatives.journal"
    new_alt: Path = ledger / "2026" / "2026-03" / "self.alternatives.journal"

    for path in (old_j, new_j):
        await path.write_text('include "preludes/self.journal"\n')
    for path in (old_alt, new_alt):
        await path.write_text('include "preludes/self.alternatives.journal"\n')
    old_alt_before = await old_alt.read_text()
    new_alt_before = await new_alt.read_text()

    monkeypatch.setattr(clopen, "get_ledger_folder", lambda: ledger)

    async def fake_run_hledger(journal: PathLike[str], *args: object):
        """Return canned closing/opening output for ``journal``."""

        return (f"{CLOSING_TX}\n\n{OPENING_TX}\n", "", 0)

    monkeypatch.setattr(clopen, "run_hledger", fake_run_hledger)

    args = clopen.Arguments(command="close", period="2026-02", files=("self.journal",))
    assert await clopen.main(args) == 0

    assert "2026-02-28 closing balances" in await old_j.read_text()
    assert "2026-03-01 opening balances" in await new_j.read_text()
    # the alternatives journals are left byte-identical
    assert await old_alt.read_text() == old_alt_before
    assert await new_alt.read_text() == new_alt_before


@pytest.mark.anyio
async def test_files_unmatched_name_processes_the_rest(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A name matching no journal must not raise nor block the other names."""

    ledger: Path = Path(tmp_path) / "ledger"
    await (ledger / "2026" / "2026-02").mkdir(parents=True)
    await (ledger / "2026" / "2026-03").mkdir(parents=True)

    old_j: Path = ledger / "2026" / "2026-02" / "self.journal"
    new_j: Path = ledger / "2026" / "2026-03" / "self.journal"
    old_alt: Path = ledger / "2026" / "2026-02" / "self.alternatives.journal"

    await old_j.write_text('include "preludes/self.journal"\n')
    await new_j.write_text('include "preludes/self.journal"\n')
    await old_alt.write_text('include "preludes/self.alternatives.journal"\n')
    old_alt_before = await old_alt.read_text()

    monkeypatch.setattr(clopen, "get_ledger_folder", lambda: ledger)

    async def fake_run_hledger(journal: PathLike[str], *args: object):
        """Return canned closing/opening output for ``journal``."""

        return (f"{CLOSING_TX}\n\n{OPENING_TX}\n", "", 0)

    monkeypatch.setattr(clopen, "run_hledger", fake_run_hledger)

    args = clopen.Arguments(
        command="close",
        period="2026-02",
        files=("self.investments.journal", "self.journal"),
    )
    assert await clopen.main(args) == 0

    assert "2026-02-28 closing balances" in await old_j.read_text()
    assert "2026-03-01 opening balances" in await new_j.read_text()
    assert await old_alt.read_text() == old_alt_before


@pytest.mark.anyio
async def test_files_empty_sequence_processes_nothing(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """An empty ``files`` sequence processes no journal at all."""

    ledger: Path = Path(tmp_path) / "ledger"
    await (ledger / "2026" / "2026-02").mkdir(parents=True)
    await (ledger / "2026" / "2026-03").mkdir(parents=True)

    old_j: Path = ledger / "2026" / "2026-02" / "self.journal"
    new_j: Path = ledger / "2026" / "2026-03" / "self.journal"
    old_alt: Path = ledger / "2026" / "2026-02" / "self.alternatives.journal"
    new_alt: Path = ledger / "2026" / "2026-03" / "self.alternatives.journal"

    for path in (old_j, new_j):
        await path.write_text('include "preludes/self.journal"\n')
    for path in (old_alt, new_alt):
        await path.write_text('include "preludes/self.alternatives.journal"\n')
    before = {path: await path.read_text() for path in (old_j, new_j, old_alt, new_alt)}

    monkeypatch.setattr(clopen, "get_ledger_folder", lambda: ledger)

    async def fake_run_hledger(journal: PathLike[str], *args: object):
        """Return canned closing/opening output for ``journal``."""

        return (f"{CLOSING_TX}\n\n{OPENING_TX}\n", "", 0)

    monkeypatch.setattr(clopen, "run_hledger", fake_run_hledger)

    args = clopen.Arguments(command="close", period="2026-02", files=())
    assert await clopen.main(args) == 0

    for path, text in before.items():
        assert await path.read_text() == text


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

    args = clopen.Arguments(command="close", period="2026-02")
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
    ns: Namespace = p.parse_args(["close", "2026-02"])

    # the invoke coroutine returns None
    await ns.invoke(ns)
    assert isinstance(called.get("args"), clopen.Arguments)
    assert called["args"].command == "close"
    assert called["args"].period == "2026-02"


@pytest.mark.anyio
async def test_parser_collects_journal_filenames(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each journal filename after the period is collected into ``Arguments``."""

    called: dict[str, clopen.Arguments] = {}

    async def fake_main(args: clopen.Arguments) -> None:
        """Capture the arguments passed by the parser's ``invoke`` callback."""

        called["args"] = args

    monkeypatch.setattr(clopen, "main", fake_main)
    p: ArgumentParser = clopen.parser()
    ns: Namespace = p.parse_args(
        ["close", "2026-02", "self.journal", "self.alternatives.journal"]
    )

    await ns.invoke(ns)
    assert called["args"].command == "close"
    assert called["args"].period == "2026-02"
    assert called["args"].files == ("self.journal", "self.alternatives.journal")


def test_close_parses_period_and_files() -> None:
    """The close subcommand accepts a period and journal filenames."""

    args = clopen.parser().parse_args(
        ["close", "2026-06", "ledger/2026/2026-06/self.journal"]
    )
    assert args.command == "close"
    assert args.period == "2026-06"
    assert args.files == ["ledger/2026/2026-06/self.journal"]


def test_verify_parses_its_three_arguments() -> None:
    """The declared verify subcommand takes a period, filenames, and ``--now``."""

    args = clopen.parser().parse_args(
        ["verify", "2026-06", "self.journal", "--now", "2026-11"]
    )
    assert args.command == "verify"
    assert args.period == "2026-06"
    assert args.files == ["self.journal"]
    assert args.now == "2026-11"

    bare = clopen.parser().parse_args(["verify"])
    assert (bare.period, bare.files, bare.now) == (None, [], None)


def test_no_subcommand_exits_two(capsys: pytest.CaptureFixture[str]) -> None:
    """Running the tool with no subcommand prints usage and exits 2."""

    with pytest.raises(SystemExit) as excinfo:
        clopen.parser().parse_args([])
    assert excinfo.value.code == 2
    usage = capsys.readouterr().err
    assert "close" in usage
    assert "verify" in usage


@pytest.mark.anyio
async def test_main_dispatches_to_verify(monkeypatch: pytest.MonkeyPatch) -> None:
    """The dispatcher forwards a verify subcommand and returns its code."""

    calls: list[clopen.Arguments] = []

    async def fake_verify(args: clopen.Arguments) -> int:
        """Record the arguments and report a failing exit code."""

        calls.append(args)
        return 1

    monkeypatch.setattr(clopen, "verify", fake_verify)

    code = await clopen.main(clopen.Arguments(command="verify", now="2026-11"))

    assert code == 1
    assert calls == [clopen.Arguments(command="verify", now="2026-11")]


def test_module_main_invokes_run(run_module_helper: RunModuleHelper) -> None:
    """Running the module as a script should ultimately call ``runnify``.

    This mirrors the tests present for the other helper scripts.
    """

    called = run_module_helper("scripts.clopen", ["scripts.clopen", "close", "2026-02"])
    assert called["ran"] is True


"""Account declarations shared by every fixture journal.

The verifier decides which accounts a closing must zero from
``hledger accounts --types``, so the types are declared explicitly rather than
left to hledger's name inference.
"""
_DECLARATIONS = """\
account assets:bank                ; type: A
account assets:cash                ; type: C
account equity:opening/closing balances
account expenses:food              ; type: X
"""


"""A clean April whose opening, activity, and closing all agree."""
_CLEAN_APRIL = """\
2026-04-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:cash                      100.00 HKD = 100.00 HKD
    equity:opening/closing balances

2026-04-10 lunch
    expenses:food                     10.00 HKD
    assets:cash                      -10.00 HKD

2026-04-30 closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00
    assets:cash                      -90.00 HKD = 0.00 HKD
    equity:opening/closing balances   90.00 HKD
"""


def _write_named(folder: StdPath, month: str, name: str, text: str) -> StdPath:
    """Write ``text`` as ``folder/<month>/<name>``, declarations included."""
    directory = folder / month
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_text(f"{_DECLARATIONS}\n{text}")
    return path


def _write_journal(folder: StdPath, month: str, text: str) -> StdPath:
    """Write ``text`` as the monthly journal ``folder/<month>/self.journal``.

    Returns the journal path so a test can pass it straight to the verifier.
    """
    return _write_named(folder, month, "self.journal", text)


def _clean_month(month: str, balance: str) -> str:
    """Return a boundary-only journal for ``month`` whose cash opens at ``balance``.

    The balancing side is left unstated, so hledger infers it and the month
    stays clean whatever the opening balance is.
    """
    year, number = month.split("-")
    last = f"{month}-{monthrange(int(year), int(number))[1]:02d}"
    return (
        f"{month}-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00\n"
        f"    assets:cash                      {balance} HKD = {balance} HKD\n"
        "    equity:opening/closing balances\n"
        "\n"
        f"{last} closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00\n"
        f"    assets:cash                     -{balance} HKD = 0.00 HKD\n"
        "    equity:opening/closing balances\n"
    )


def _kinds(defects: Sequence[clopen.Defect]) -> list[tuple[str, str]]:
    """Return the (month, kind) pair of every defect, for compact assertions."""
    return [(defect.month, defect.kind) for defect in defects]


@pytest.mark.anyio
async def test_clean_chain_reports_nothing(tmp_path: PathLike[str]) -> None:
    """A month whose opening and closing match its activity yields no defect."""

    folder = StdPath(tmp_path) / "ledger" / "2026"
    april = _write_journal(folder, "2026-04", _CLEAN_APRIL)
    may = _write_journal(
        folder,
        "2026-05",
        """\
2026-05-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:cash                       90.00 HKD = 90.00 HKD
    equity:opening/closing balances

2026-05-20 lunch
    expenses:food                     30.00 HKD
    assets:cash                      -30.00 HKD

2026-05-31 closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00
    assets:cash                      -60.00 HKD = 0.00 HKD
    equity:opening/closing balances   60.00 HKD
""",
    )

    defects = await clopen.verify_family([april, may], "2026-06")

    assert list(defects) == []


@pytest.mark.anyio
async def test_missing_closing_reported(tmp_path: PathLike[str]) -> None:
    """A month before the current one without a closing reports the omission."""

    folder = StdPath(tmp_path) / "ledger" / "2026"
    april = _write_journal(
        folder,
        "2026-04",
        """\
2026-04-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:cash                      100.00 HKD = 100.00 HKD
    equity:opening/closing balances

2026-04-10 lunch
    expenses:food                     10.00 HKD
    assets:cash                      -10.00 HKD
""",
    )

    defects = await clopen.verify_family([april], "2026-06")

    assert _kinds(defects) == [("2026-04", "missing_closing")]


@pytest.mark.anyio
async def test_missing_opening_reported(tmp_path: PathLike[str]) -> None:
    """A month before the current one without an opening reports the omission."""

    folder = StdPath(tmp_path) / "ledger" / "2026"
    april = _write_journal(
        folder,
        "2026-04",
        """\
2026-04-10 lunch
    expenses:food                     10.00 HKD
    assets:cash                      -10.00 HKD

2026-04-30 closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00
    assets:cash                       10.00 HKD = 0.00 HKD
    equity:opening/closing balances  -10.00 HKD
""",
    )

    defects = await clopen.verify_family([april], "2026-06")

    assert _kinds(defects) == [("2026-04", "missing_opening")]


@pytest.mark.anyio
async def test_opening_mismatch_reported(tmp_path: PathLike[str]) -> None:
    """An opening one cent away from negating the previous closing is reported."""

    folder = StdPath(tmp_path) / "ledger" / "2026"
    april = _write_journal(folder, "2026-04", _CLEAN_APRIL)
    may = _write_journal(
        folder,
        "2026-05",
        """\
2026-05-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:cash                       90.01 HKD = 90.01 HKD
    equity:opening/closing balances

2026-05-20 lunch
    expenses:food                     30.00 HKD
    assets:cash                      -30.00 HKD

2026-05-31 closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00
    assets:cash                      -60.01 HKD = 0.00 HKD
    equity:opening/closing balances   60.01 HKD
""",
    )

    defects = await clopen.verify_family([april, may], "2026-06")

    assert _kinds(defects) == [("2026-05", "opening_mismatch")]
    assert defects[0].detail == (
        "assets:cash: opening 2026-05 has 90.01 HKD, closing 2026-04 has -90.00 HKD"
    )


@pytest.mark.anyio
async def test_closing_incomplete_reported(tmp_path: PathLike[str]) -> None:
    """A closing that omits a funded account reports the balance it left open."""

    folder = StdPath(tmp_path) / "ledger" / "2026"
    april = _write_journal(
        folder,
        "2026-04",
        """\
2026-04-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:cash                      100.00 HKD = 100.00 HKD
    equity:opening/closing balances

2026-04-10 transfer
    assets:bank                       50.00 HKD
    assets:cash                      -50.00 HKD

2026-04-30 closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00
    assets:cash                      -50.00 HKD = 0.00 HKD
    equity:opening/closing balances   50.00 HKD
""",
    )

    defects = await clopen.verify_family([april], "2026-06")

    assert _kinds(defects) == [("2026-04", "closing_incomplete")]
    assert defects[0].detail == "assets:bank: 50.00 HKD left unclosed"


@pytest.mark.anyio
async def test_closing_amount_wrong_reported(tmp_path: PathLike[str]) -> None:
    """A closing whose amount is not the negated balance is reported.

    hledger rejects a same-commodity assertion that the amount fails, so the
    only journal that reaches this check is one whose zero assertion names a
    different commodity than the balance the closing was meant to zero.
    """

    folder = StdPath(tmp_path) / "ledger" / "2026"
    april = _write_journal(
        folder,
        "2026-04",
        """\
2026-04-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:cash                      100.00 HKD = 100.00 HKD
    equity:opening/closing balances

2026-04-10 lunch
    expenses:food                     10.00 HKD
    assets:cash                      -10.00 HKD

2026-04-30 closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00
    assets:cash                      -89.99 HKD = 0.00 USD
    equity:opening/closing balances   89.99 HKD
""",
    )

    defects = await clopen.verify_family([april], "2026-06")

    assert _kinds(defects) == [("2026-04", "closing_not_zero")]
    assert defects[0].detail == ("assets:cash: expected -90.00 HKD, found -89.99 HKD")


@pytest.mark.anyio
async def test_closing_without_zero_assertion_reported(
    tmp_path: PathLike[str],
) -> None:
    """A closing posting that does not assert a zero balance is reported."""

    folder = StdPath(tmp_path) / "ledger" / "2026"
    april = _write_journal(
        folder,
        "2026-04",
        """\
2026-04-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:cash                      100.00 HKD = 100.00 HKD
    equity:opening/closing balances

2026-04-10 lunch
    expenses:food                     10.00 HKD
    assets:cash                      -10.00 HKD

2026-04-30 closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00
    assets:cash                      -90.00 HKD
    equity:opening/closing balances   90.00 HKD
""",
    )

    defects = await clopen.verify_family([april], "2026-06")

    assert _kinds(defects) == [("2026-04", "closing_not_zero")]
    assert defects[0].detail == (
        "assets:cash: closing posting has no balance assertion"
    )


@pytest.mark.anyio
async def test_future_month_boundary_reported(tmp_path: PathLike[str]) -> None:
    """Boundaries in a month after the current one are unexpected."""

    folder = StdPath(tmp_path) / "ledger" / "2026"
    april = _write_journal(
        folder,
        "2026-04",
        """\
2026-04-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:cash                      100.00 HKD = 100.00 HKD
    equity:opening/closing balances

2026-04-30 closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00
    assets:cash                     -100.00 HKD = 0.00 HKD
    equity:opening/closing balances  100.00 HKD
""",
    )
    may = _write_journal(
        folder,
        "2026-05",
        """\
2026-05-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:cash                      100.00 HKD = 100.00 HKD
    equity:opening/closing balances

2026-05-31 closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00
    assets:cash                     -100.00 HKD = 0.00 HKD
    equity:opening/closing balances  100.00 HKD
""",
    )

    defects = await clopen.verify_family([april, may], "2026-04")

    assert _kinds(defects) == [
        ("2026-05", "unexpected_boundary"),
        ("2026-05", "unexpected_boundary"),
    ]
    assert [defect.detail for defect in defects] == [
        "closing balances transaction in a month after 2026-04",
        "opening balances transaction in a month after 2026-04",
    ]


@pytest.mark.anyio
async def test_closing_not_last_reported(tmp_path: PathLike[str]) -> None:
    """A transaction after the closing leaves the closing out of place."""

    folder = StdPath(tmp_path) / "ledger" / "2026"
    april = _write_journal(
        folder,
        "2026-04",
        """\
2026-04-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:cash                      100.00 HKD = 100.00 HKD
    equity:opening/closing balances

2026-04-10 lunch
    expenses:food                     10.00 HKD
    assets:cash                      -10.00 HKD

2026-04-30 closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00
    assets:cash                      -90.00 HKD = 0.00 HKD
    equity:opening/closing balances   90.00 HKD

2026-04-30 adjustment
    expenses:food                      1.00 HKD
    assets:cash                       -1.00 HKD
""",
    )

    defects = await clopen.verify_family([april], "2026-06")

    assert _kinds(defects) == [("2026-04", "boundary_unordered")]
    assert defects[0].detail == "closing balances is not the last transaction"


@pytest.mark.anyio
async def test_boundary_date_and_time_reported(tmp_path: PathLike[str]) -> None:
    """An opening off its date and time is reported for both."""

    folder = StdPath(tmp_path) / "ledger" / "2026"
    april = _write_journal(
        folder,
        "2026-04",
        """\
2026-04-02 opening balances  ; clopen: , time: 00:00:01, timezone: UTC+08:00
    assets:cash                      100.00 HKD = 100.00 HKD
    equity:opening/closing balances

2026-04-30 closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00
    assets:cash                     -100.00 HKD = 0.00 HKD
    equity:opening/closing balances  100.00 HKD
""",
    )

    defects = await clopen.verify_family([april], "2026-06")

    assert _kinds(defects) == [
        ("2026-04", "boundary_unordered"),
        ("2026-04", "boundary_unordered"),
    ]
    assert [defect.detail for defect in defects] == [
        "opening balances has time 00:00:01, expected 00:00:00",
        "opening balances is dated 2026-04-02, expected 2026-04-01",
    ]


@pytest.mark.anyio
async def test_now_override_classifies_current_month(tmp_path: PathLike[str]) -> None:
    """The current month keeps its closing optional; an earlier view requires it."""

    folder = StdPath(tmp_path) / "ledger" / "2026"
    may = _write_journal(
        folder,
        "2026-05",
        """\
2026-05-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:cash                      100.00 HKD = 100.00 HKD
    equity:opening/closing balances

2026-05-20 lunch
    expenses:food                     30.00 HKD
    assets:cash                      -30.00 HKD
""",
    )

    assert list(await clopen.verify_family([may], "2026-05")) == []
    assert _kinds(await clopen.verify_family([may], "2026-06")) == [
        ("2026-05", "missing_closing")
    ]
    assert _kinds(await clopen.verify_family([may], "2026-04")) == [
        ("2026-05", "unexpected_boundary"),
    ]


@pytest.mark.anyio
async def test_closing_asserting_nonzero_reported(tmp_path: PathLike[str]) -> None:
    """A closing that asserts a non-zero balance is reported twice over.

    hledger accepts an assertion that holds, so a closing posting can assert the
    very balance it was meant to zero out: the assertion rule and the amount
    rule then both speak about the same account.
    """

    folder = StdPath(tmp_path) / "ledger" / "2026"
    april = _write_journal(
        folder,
        "2026-04",
        """\
2026-04-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:bank                       5.00 HKD = 5.00 HKD
    equity:opening/closing balances

2026-04-30 closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00
    assets:bank                      = 5.00 HKD
    equity:opening/closing balances
""",
    )

    defects = await clopen.verify_family([april], "2026-06")

    assert _kinds(defects) == [
        ("2026-04", "closing_not_zero"),
        ("2026-04", "closing_not_zero"),
    ]
    assert [defect.detail for defect in defects] == [
        "assets:bank: closing posting asserts 5.00 HKD instead of zero",
        "assets:bank: expected -5.00 HKD, found 0.00 HKD",
    ]


@pytest.mark.anyio
async def test_closing_date_and_time_reported(tmp_path: PathLike[str]) -> None:
    """A closing off its date and time is reported for both."""

    folder = StdPath(tmp_path) / "ledger" / "2026"
    april = _write_journal(
        folder,
        "2026-04",
        """\
2026-04-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:cash                      100.00 HKD = 100.00 HKD
    equity:opening/closing balances

2026-04-29 closing balances  ; clopen: , time: 23:59:58, timezone: UTC+08:00
    assets:cash                     -100.00 HKD = 0.00 HKD
    equity:opening/closing balances  100.00 HKD
""",
    )

    defects = await clopen.verify_family([april], "2026-06")

    assert _kinds(defects) == [
        ("2026-04", "boundary_unordered"),
        ("2026-04", "boundary_unordered"),
    ]
    assert [defect.detail for defect in defects] == [
        "closing balances has time 23:59:58, expected 23:59:59",
        "closing balances is dated 2026-04-29, expected 2026-04-30",
    ]


@pytest.mark.anyio
async def test_unreadable_journal_reported(tmp_path: PathLike[str]) -> None:
    """A journal hledger cannot read becomes an unreadable defect."""

    folder = StdPath(tmp_path) / "ledger" / "2026"
    broken = _write_journal(folder, "2026-04", "2026-13-01 not a month\n")

    defects = await clopen.verify_family([broken], "2026-06")

    assert _kinds(defects) == [("2026-04", "unreadable")]
    assert defects[0].detail.startswith("hledger print exited 1: ")


def _write_chain(folder: StdPath) -> list[StdPath]:
    """Write one clean and one closing-less month, in two journal families."""
    june = _write_journal(
        folder,
        "2026-06",
        """\
2026-06-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:cash                      100.00 HKD = 100.00 HKD
    equity:opening/closing balances
""",
    )
    alternatives = june.with_name("self.alternatives.journal")
    alternatives.write_text(june.read_text())
    return [june, alternatives]


@pytest.mark.anyio
async def test_verify_prints_defects_and_returns_one(
    tmp_path: PathLike[str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The subcommand prints one line per defect and returns a failing code."""

    ledger = StdPath(tmp_path) / "ledger"
    journals = _write_chain(ledger / "2026")
    monkeypatch.setattr(clopen, "get_ledger_folder", lambda: ledger)

    code = await clopen.verify(clopen.Arguments(command="verify", now="2026-07"))

    assert code == 1
    printed = sorted(capsys.readouterr().out.splitlines())
    assert printed == sorted(
        f"{journal.resolve()}:2026-06: missing_closing: no closing balances transaction"
        for journal in journals
    )


@pytest.mark.anyio
async def test_verify_filters_by_period_and_file(
    tmp_path: PathLike[str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The period and the filenames narrow the journals that are reported."""

    ledger = StdPath(tmp_path) / "ledger"
    journals = _write_chain(ledger / "2026")
    monkeypatch.setattr(clopen, "get_ledger_folder", lambda: ledger)

    code = await clopen.verify(
        clopen.Arguments(
            command="verify", now="2026-07", period="2026-06", files=("self.journal",)
        )
    )

    assert code == 1
    assert capsys.readouterr().out.splitlines() == [
        f"{journals[0].resolve()}:2026-06: missing_closing: "
        "no closing balances transaction"
    ]


@pytest.mark.anyio
async def test_verify_returns_zero_when_clean(
    tmp_path: PathLike[str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A clean chain prints nothing and returns zero."""

    ledger = StdPath(tmp_path) / "ledger"
    _write_journal(
        ledger / "2026",
        "2026-06",
        """\
2026-06-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:cash                      100.00 HKD = 100.00 HKD
    equity:opening/closing balances

2026-06-30 closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00
    assets:cash                     -100.00 HKD = 0.00 HKD
    equity:opening/closing balances  100.00 HKD
""",
    )
    monkeypatch.setattr(clopen, "get_ledger_folder", lambda: ledger)

    code = await clopen.verify(
        clopen.Arguments(
            command="verify", now="2026-06", period="2026-06", files=("self.journal",)
        )
    )

    assert code == 0
    assert capsys.readouterr().out == ""


@pytest.mark.anyio
async def test_account_types_failure_reported(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failing ``accounts --types`` call is reported instead of guessed around."""

    folder = StdPath(tmp_path) / "ledger" / "2026"
    april = _write_journal(folder, "2026-04", _CLEAN_APRIL)
    real_run_hledger = clopen.run_hledger

    async def fake_run_hledger(
        journal: PathLike[str] | str,
        *args: str,
        strict: bool = True,
        raise_on_error: bool = True,
        log_on_error: bool = True,
    ) -> tuple[str, str, int]:
        """Fail the ``accounts`` call and leave the ``print`` call alone."""
        if args[:1] == ("accounts",):
            return "", "boom\n", 2
        return await real_run_hledger(
            journal,
            *args,
            strict=strict,
            raise_on_error=raise_on_error,
            log_on_error=log_on_error,
        )

    monkeypatch.setattr(clopen, "run_hledger", fake_run_hledger)

    defects = await clopen.verify_family([april], "2026-06")

    assert _kinds(defects) == [("2026-04", "unreadable")]
    assert defects[0].detail == "hledger accounts --types exited 2: boom"


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("stdout", "detail"),
    [
        ("", "hledger print produced no output"),
        ("not json", "hledger print produced an unexpected document"),
    ],
)
async def test_invalid_hledger_output_reported(
    tmp_path: PathLike[str],
    monkeypatch: pytest.MonkeyPatch,
    stdout: str,
    detail: str,
) -> None:
    """Output hledger cannot have produced becomes an unreadable defect."""

    folder = StdPath(tmp_path) / "ledger" / "2026"
    april = _write_journal(folder, "2026-04", _CLEAN_APRIL)

    async def fake_run_hledger(
        journal: PathLike[str] | str,
        *args: str,
        strict: bool = True,
        raise_on_error: bool = True,
        log_on_error: bool = True,
    ) -> tuple[str, str, int]:
        """Return the given output as if hledger had printed it."""
        return stdout, "", 0

    monkeypatch.setattr(clopen, "run_hledger", fake_run_hledger)

    defects = await clopen.verify_family([april], "2026-06")

    assert _kinds(defects) == [("2026-04", "unreadable")]
    assert defects[0].detail.startswith(detail)


@pytest.mark.anyio
async def test_parser_builds_verify_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    """The verifier subcommand collects its three arguments into one container."""

    captured: list[clopen.Arguments] = []

    async def fake_main(args: clopen.Arguments) -> int:
        """Record the arguments instead of verifying the ledger."""
        captured.append(args)
        return 0

    monkeypatch.setattr(clopen, "main", fake_main)

    entry = clopen.parser().parse_args(
        [
            "verify",
            "2026-06",
            "self.journal",
            "self.alternatives.journal",
            "--now",
            "2026-06-30",
        ]
    )
    await entry.invoke(entry)

    assert captured == [
        clopen.Arguments(
            command="verify",
            period="2026-06",
            files=("self.journal", "self.alternatives.journal"),
            now="2026-06-30",
        )
    ]


@pytest.mark.anyio
async def test_current_month_missing_opening_reported(tmp_path: PathLike[str]) -> None:
    """The current month needs its opening but not its closing."""

    folder = StdPath(tmp_path) / "ledger" / "2026"
    june = _write_journal(
        folder,
        "2026-06",
        """\
2026-06-10 lunch
    expenses:food                     10.00 HKD
    assets:cash                      -10.00 HKD
""",
    )

    defects = await clopen.verify_family([june], "2026-06")

    assert _kinds(defects) == [("2026-06", "missing_opening")]


@pytest.mark.anyio
async def test_journal_families_are_not_compared(tmp_path: PathLike[str]) -> None:
    """Two journal families in one month are never compared with each other."""

    folder = StdPath(tmp_path) / "ledger" / "2026"
    main_journal = _write_journal(folder, "2026-04", _clean_month("2026-04", "90.00"))
    alternatives = _write_named(
        folder,
        "2026-04",
        "self.alternatives.journal",
        _clean_month("2026-04", "500.00"),
    )

    defects = await clopen.verify_family([main_journal, alternatives], "2026-05")

    assert list(defects) == []


@pytest.mark.anyio
async def test_duplicate_boundary_reported(tmp_path: PathLike[str]) -> None:
    """Two closing transactions in one month are reported, not silently picked."""

    folder = StdPath(tmp_path) / "ledger" / "2026"
    april = _write_journal(
        folder,
        "2026-04",
        """\
2026-04-01 opening balances  ; clopen: , time: 00:00:00, timezone: UTC+08:00
    assets:cash                      100.00 HKD = 100.00 HKD
    equity:opening/closing balances

2026-04-15 closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00
    assets:cash                     -100.00 HKD = 0.00 HKD
    equity:opening/closing balances

2026-04-30 closing balances  ; clopen: , time: 23:59:59, timezone: UTC+08:00
    assets:cash                        0.00 HKD = 0.00 HKD
    equity:opening/closing balances
""",
    )

    defects = await clopen.verify_family([april], "2026-05")

    assert _kinds(defects) == [("2026-04", "boundary_unordered")]
    assert defects[0].detail == "2 closing balances transactions"


@pytest.mark.anyio
async def test_unreadable_month_breaks_the_chain(tmp_path: PathLike[str]) -> None:
    """A month that cannot be read leaves its neighbours unpaired."""

    folder = StdPath(tmp_path) / "ledger" / "2026"
    march = _write_journal(folder, "2026-03", _clean_month("2026-03", "90.00"))
    april = _write_journal(folder, "2026-04", "2026-13-01 not a month\n")
    may = _write_journal(folder, "2026-05", _clean_month("2026-05", "500.00"))

    defects = await clopen.verify_family([march, april, may], "2026-06")

    assert _kinds(defects) == [("2026-04", "unreadable")]


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("month", "detail"),
    [
        ("june", "month directory 'june' is not named YYYY-MM"),
        ("2026-13", "month directory '2026-13' is not a calendar month"),
    ],
)
async def test_malformed_month_directory_reported(
    tmp_path: PathLike[str], month: str, detail: str
) -> None:
    """A directory that is not a month is a defect, not a crash."""

    folder = StdPath(tmp_path) / "ledger" / "2026"
    journal = _write_journal(folder, month, _clean_month("2026-04", "90.00"))

    defects = await clopen.verify_family([journal], "2026-06")

    assert _kinds(defects) == [(month, "unreadable")]
    assert defects[0].detail == detail


@pytest.mark.anyio
async def test_verify_rejects_malformed_period(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A period that is not a month is rejected instead of selecting nothing."""

    monkeypatch.setattr(clopen, "get_ledger_folder", lambda: StdPath(tmp_path))

    with pytest.raises(ValueError, match="period '2026-1' is not a YYYY-MM month"):
        await clopen.verify(
            clopen.Arguments(command="verify", period="2026-1", now="2026-11")
        )


@pytest.mark.anyio
async def test_verify_rejects_unknown_file(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A filename that matches no journal is rejected instead of selecting nothing."""

    folder = StdPath(tmp_path) / "ledger" / "2026"
    _write_journal(folder, "2026-06", _clean_month("2026-06", "90.00"))
    monkeypatch.setattr(
        clopen, "get_ledger_folder", lambda: StdPath(tmp_path) / "ledger"
    )

    with pytest.raises(
        ValueError, match="journal filename 'ledger/2026/2026-06/self.journal'"
    ):
        await clopen.verify(
            clopen.Arguments(
                command="verify",
                files=("ledger/2026/2026-06/self.journal",),
                now="2026-11",
            )
        )


@pytest.mark.anyio
async def test_main0_reports_argument_errors(
    tmp_path: PathLike[str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A rejected argument exits non-zero with one line naming it."""

    monkeypatch.setattr(clopen, "get_ledger_folder", lambda: StdPath(tmp_path))
    monkeypatch.setattr(clopen.sys, "argv", ["clopen", "verify", "2026-1"])

    with pytest.raises(SystemExit) as exit_info:
        await clopen.main0()

    assert exit_info.value.code == 1
    assert capsys.readouterr().err == (
        "error: period '2026-1' is not a YYYY-MM month\n"
    )
