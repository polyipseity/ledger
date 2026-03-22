"""Create closing and opening balance entries for monthly journals.

This script runs ``hledger close --explicit --show-costs --clopen`` on each
journal file for the supplied period and writes the resulting closing
transaction to the end of the existing journal. The corresponding opening
transaction is prepended to the beginning of the *next* month's journal after
any ``include`` directives.

Usage example:

    python -m scripts.clopen 2026-02

The script performs safety checks before writing:

* if the closing transaction already appears in the old journal it errors out
  without modifying anything.
* if the opening transaction already appears in the next journal it errors
  out as well.
* if the next-month journal cannot be found the script logs an informational
  message and **still appends the closing transaction**; the opening side will
  be written later when the journal is created.  This allows the user to run
  the tool before the next period exists.

The command is intentionally conservative; aside from the missing-next-month
scenario described above, any pre-existing balances cause a failure so that
the user can investigate before the script mutates files.

The implementation mirrors the style of the other helper scripts in
``scripts/`` and provides a full test suite under ``tests/scripts_``.
"""

from argparse import ArgumentParser, Namespace
from calendar import monthrange
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from logging import INFO, basicConfig, info
from os import PathLike
from sys import argv, exit
from typing import final

from anyio import Path
from asyncer import runnify

from .utils.cache import JournalRunContext
from .utils.files import file_update_if_changed, get_ledger_folder
from .utils.journals import (
    filter_journals_between,
    find_monthly_journals,
    format_journal_list,
    parse_period_start,
    run_hledger,
)

"""Public symbols exported by this module."""
__all__ = ("Arguments", "main", "parser")


@final
@dataclass(
    init=True,
    repr=True,
    eq=True,
    order=False,
    unsafe_hash=False,
    frozen=True,
    match_args=True,
    kw_only=True,
    slots=True,
)
class Arguments:
    """Command-line arguments container for :mod:`scripts.clopen`.

    Attributes:
        period: A year-month string (e.g. ``"2026-02"``) specifying which
            monthly folder to process. The script will operate on every
            ``*.journal`` file found under the corresponding ``ledger/YYYY/YYYY-MM``
            directory.
    """

    period: str


async def _process_journal(journal: PathLike[str]) -> None:
    """Process a single journal file, appending closing and prepending opening.

    The helper performs all of the safety checks described in the module
    docstring. It uses :func:`run_hledger` to obtain the clopen transactions and
    writes them back to the appropriate files using
    :func:`file_update_if_changed`.
    """

    p = Path(journal)

    # run hledger to compute the closing/opening transactions
    stdout, _stderr, _rc = await run_hledger(
        journal,
        "close",
        "--explicit",
        "--show-costs",
        "--clopen",
    )
    text = stdout.strip()
    if not text:
        raise ValueError(f"hledger produced no output for {journal}")

    parts = text.split("\n\n", 1)
    if len(parts) != 2:
        raise ValueError(f"unexpected hledger output format for {journal}\n{text}")

    closing, opening = parts

    # compute the correct dates based on the journal folder; hledger output may
    # include garbage dates so we override the first line of each transaction.
    try:
        year_str, month_str = p.parent.name.split("-")
        year = int(year_str)
        month = int(month_str)
    except Exception:
        raise ValueError(f"unable to parse year-month from {p.parent}")

    # closing date is the last day of the month at whatever day hledger
    # produced; opening is the first of the following month.

    last_day = monthrange(year, month)[1]
    closing_date = f"{year:04d}-{month:02d}-{last_day:02d}"
    if month == 12:
        next_year = year + 1
        next_month = 1
    else:
        next_year = year
        next_month = month + 1
    opening_date = f"{next_year:04d}-{next_month:02d}-01"

    def _rewrite_date(tx: str, new_date: str) -> str:
        """Return ``tx`` with its first-line date replaced by ``new_date``."""

        lines = tx.splitlines()
        if lines:
            parts = lines[0].split(" ", 1)
            if len(parts) > 1:
                lines[0] = f"{new_date} {parts[1]}"
            else:
                lines[0] = new_date
        return "\n".join(lines)

    def _add_tags(tx: str, time_tag: str) -> str:
        """Ensure the first line of ``tx`` contains sorted tags.

        The tags we care about are ``clopen:``, ``time: <time_tag>`` and
        ``timezone: UTC+08:00``.  They are appended to any existing comment
        and then sorted alphabetically by key so the output is deterministic.
        """
        lines = tx.splitlines()
        if not lines:
            return tx
        first = lines[0]
        if "  ;" in first:
            code, comment = first.split("  ;", 1)
            comment = comment.strip()
        else:
            code, comment = first, ""
        parts = [p.strip() for p in comment.split(",") if p.strip()]
        # add or overwrite clopen/time/timezone
        tags: dict[str, str] = {
            "clopen": "",
            "time": time_tag,
            "timezone": "UTC+08:00",
        }
        # remove existing occurrences of those keys
        new_parts: list[str] = []
        for part in parts:
            key = part.split(":", 1)[0].strip()
            if key in tags:
                continue
            new_parts.append(part)
        # add canonical tags
        for k, v in tags.items():
            if v == "":
                new_parts.append(f"{k}:")
            else:
                new_parts.append(f"{k}: {v}")
        # sort by key
        new_parts.sort(key=lambda x: x.split(":", 1)[0].strip())
        lines[0] = f"{code}  ; {', '.join(new_parts)}"
        return "\n".join(lines)

    closing = _rewrite_date(closing, closing_date)
    opening = _rewrite_date(opening, opening_date)
    # add canonical tags with proper times
    closing = _add_tags(closing, "23:59:59")
    opening = _add_tags(opening, "00:00:00")

    closing_first = next((line for line in closing.splitlines() if line.strip()), "")
    opening_first = next((line for line in opening.splitlines() if line.strip()), "")

    old_text = await p.read_text()
    # compare only the portion before any tags so existing lines missing tags
    # will still be detected.
    if closing_first:
        plain = closing_first.split("  ;", 1)[0]
        if plain in old_text:
            raise ValueError(f"closing balance already exists in {journal}")

    # determine location of next-month journal.  the repository supports
    # two layouts: `ledger/YYYY/YYYY-MM/` and `ledger/YYYY-MM/`.  in the first
    # case `p.parent.parent` already points at the ``YYYY`` folder; in the
    # second it points at the ledger root.  appending the ``YYYY-MM`` segment
    # to whatever is returned gives the correct directory in both cases.
    next_folder = p.parent.parent / f"{next_year:04d}-{next_month:02d}"
    next_journal = next_folder / p.name

    next_exists = await Path(next_journal).exists()
    if not next_exists:
        info(
            "next journal %s does not exist; creating and writing opening", next_journal
        )

    if next_exists:
        next_text = await Path(next_journal).read_text()
        if opening_first:
            plain_open = opening_first.split("  ;", 1)[0]
            if plain_open in next_text:
                raise ValueError(f"opening balance already exists in {next_journal}")

    # perform the file modifications (closing always)
    def append_updater(read: str) -> str:
        """Append the computed closing transaction to ``read``."""

        base = read.rstrip("\n")
        return f"{base}\n\n{closing.strip()}\n"

    await file_update_if_changed(journal, append_updater)

    if next_exists:

        def prepend_updater(read: str) -> str:
            """Insert the opening transaction after any include lines in ``read``."""

            lines = read.splitlines()
            idx = 0
            for i, line in enumerate(lines):
                if line.startswith("include "):
                    idx = i + 1
            before = lines[:idx]
            after = lines[idx:]
            # insert a blank line between includes and opening entry
            new_lines = before + [""] + [opening.strip()] + after
            result = "\n".join(new_lines)
            if not result.endswith("\n"):
                result += "\n"
            return result

        await file_update_if_changed(next_journal, prepend_updater)
    else:
        # next journal missing: create it with includes from old journal
        include_lines = [
            line for line in old_text.splitlines() if line.startswith("include ")
        ]
        content = "\n".join(include_lines)
        if content:
            content += "\n\n"
        content += opening.strip() + "\n"
        # ensure folder exists
        await Path(next_journal).parent.mkdir(parents=True, exist_ok=True)
        await Path(next_journal).write_text(content)


async def main(args: Arguments) -> None:
    """Entry point for ``scripts.clopen``.

    The function discovers journals for the supplied period, runs the
    processing helper for each, and exits with code ``0`` on success. Any
    failure during journal processing causes the script to exit with ``1``.
    """

    folder = get_ledger_folder()

    journals = await find_monthly_journals(folder, None)
    start = parse_period_start(args.period)
    # ``parse_period_end`` returns the start of the last day which would
    # accidentally exclude the journal when passed through
    # ``filter_journals_between`` (which compares against the month's end).
    # Compute an explicit end-of-month datetime instead to ensure the entire
    # requested period is included.
    last_day = monthrange(start.year, start.month)[1]
    end = start.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
    journals = filter_journals_between(journals, start, end)
    info("journals:\n%s", format_journal_list(journals, max_items=8))

    async with JournalRunContext(Path(__file__), journals, cache=False) as run:
        if run.skipped:
            info("skipped:\n%s", format_journal_list(run.skipped, max_items=8))
        overall_error = False
        # process one journal at a time so that an error in one file does not
        # cancel the other pending operations.  any failure is recorded and
        # causes the script to exit non-zero after all journals have been
        # attempted.
        for journal in run.to_process:
            try:
                await _process_journal(journal)
            except Exception as e:
                overall_error = True
                info("error processing %s: %s", journal, e)
        if overall_error:
            exit(1)

    exit(0)


def parser(parent: Callable[..., ArgumentParser] | None = None) -> ArgumentParser:
    """Construct and return the CLI ArgumentParser for the clopen script.

    The parser adds a single positional ``period`` argument and installs an
    ``invoke`` coroutine that constructs :class:`Arguments` and forwards them to
    :func:`main`.
    """

    prog = argv[0]

    parser = (ArgumentParser if parent is None else parent)(
        prog=prog,
        description="create closing/opening balance entries for a given period",
        add_help=True,
        allow_abbrev=False,
        exit_on_error=False,
    )

    parser.add_argument(
        "period",
        help="year-month to process (e.g. 2026-02)",
    )

    @wraps(main)
    async def invoke(ns: Namespace) -> None:
        """Adapter used as ``argparse`` callback to run :func:`main`."""

        await main(Arguments(period=ns.period))

    parser.set_defaults(invoke=invoke)
    return parser


if __name__ == "__main__":
    basicConfig(level=INFO)
    """Parsed CLI namespace used to invoke the entrypoint."""
    entry = parser().parse_args(argv[1:])
    runnify(entry.invoke)(entry)
