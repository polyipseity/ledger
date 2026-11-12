#!/usr/bin/env python
"""Create closing and opening balance entries, and verify the boundary chain.

``close`` runs ``hledger close --explicit --show-costs --clopen`` on each
journal file for the supplied period, or on the subset of those files named on
the command line, and writes the resulting closing transaction to the end of
the existing journal. The corresponding opening transaction is prepended to the
beginning of the *next* month's journal after any ``include`` directives.

A journal filename such as ``self.journal`` names a journal rather than a path.
Restricting the run keeps a repair from touching a journal family the month
never used.

``verify`` reads every monthly journal, classifies each one against the current
month, and reports every boundary defect as one ``journal:month: kind: detail``
line. ``hledger check`` passes on a ledger whose monthly chain is broken,
because a month that never received its ``closing balances`` transaction simply
lets the balances roll forward: no assertion is violated, so nothing else
notices, and this subcommand is the tool that does. Months before the current
month need both boundaries, the current month needs only its opening, and later
months must carry neither. On top of that presence rule, the boundaries are
checked in content: the opening must sit first in the month and the closing
last, every closing posting must assert a zero balance, every asset, cash, and
liability account with a non-zero balance must be zeroed by the closing, and
each month's opening must negate the closing of the month before it in the same
journal family. A month whose journal cannot be read reports that one defect
and breaks the chain, so its neighbours are never compared across the gap.

``verify`` is read-only by construction: it never writes a journal, never
touches the run cache, and never repairs what it reports. Every argument and
every environment failure is an error, not a defect: the exit code is ``0`` for
a clean chain and ``1`` for defects or for any error, printed as declared for
the period, the filenames, and the derived current month. The current month
comes from the committer date of the last commit (``git log -1 --format=%cI``)
rather than the author date, because a rebase, amend, or cherry-pick advances
the committer date, so it tracks when the record actually landed, whereas an
author date can survive a rebase for months.

Usage example:

    python -m scripts.clopen close 2026-02
    python -m scripts.clopen close 2026-02 self.journal
    python -m scripts.clopen verify
    python -m scripts.clopen verify --now 2026-11
    python -m scripts.clopen verify 2026-06 self.journal

The ``close`` subcommand performs safety checks before writing:

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

import sys
from argparse import ArgumentParser, Namespace
from calendar import monthrange
from collections import defaultdict
from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass
from decimal import Decimal
from functools import wraps
from logging import INFO, basicConfig, info
from os import PathLike
from pathlib import Path as StdPath
from typing import final

from anyio import Path
from asyncer import runnify

from .utils.cache import JournalRunContext
from .utils.files import file_update_if_changed, get_ledger_folder
from .utils.hledger import (
    CLOSING_DESCRIPTION,
    OPENING_DESCRIPTION,
    DefectKind,
    Journal,
    Transaction,
    Unreadable,
    display_path,
    first_line,
    hledger_output,
    last_day,
    load_journal,
    money,
)
from .utils.journals import (
    filter_journals_between,
    find_monthly_journals,
    format_journal_list,
    parse_period_start,
    resolve_now_month,
    resolve_period,
    run_hledger,
)

"""Public symbols exported by this module."""
__all__ = (
    "Arguments",
    "Defect",
    "close",
    "main",
    "parser",
    "verify",
    "verify_family",
)

"""Account that receives the balancing side of every boundary transaction.

Postings on it are exempt from every amount comparison: its amount is inferred
from the transaction rather than written, so it restates nothing.
"""
_EQUITY_ACCOUNT = "equity:opening/closing balances"
"""Account types, as ``hledger accounts --types`` spells them, that a closing must zero.

Asset, cash, and liability accounts carry a balance forward, so leaving one out
of a closing loses it. Equity, revenue, and expense accounts do not: hledger's
own ``close`` command zeroes only these three types.
"""
_CLOSED_TYPES = frozenset({"A", "C", "L"})
"""Detail reported when a month that requires an opening balance has none."""
_MISSING_OPENING = "no opening balances transaction"
"""Detail reported when a month that requires a closing balance has none."""
_MISSING_CLOSING = "no closing balances transaction"


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
        command: The subcommand to run, ``"close"`` or ``"verify"``.
        period: A year-month string (e.g. ``"2026-02"``) specifying which
            monthly folder to process. ``close`` requires it, and operates on
            every ``*.journal`` file found under the corresponding
            ``ledger/YYYY/YYYY-MM`` directory unless ``files`` narrows that set.
            ``verify`` treats ``None`` as every month.
        files: Journal filenames (e.g. ``"self.journal"``, not paths) to
            restrict processing to. ``None`` processes every journal of the
            period; an empty sequence processes nothing. A name that matches
            no journal of the period is ignored by ``close``.
        now: The month ``verify`` treats as current, as ``YYYY-MM`` or an ISO
            date. ``None`` derives it from the last commit date. ``close``
            ignores it.
    """

    command: str
    period: str | None = None
    files: tuple[str, ...] | None = None
    now: str | None = None


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

    days_in_month = monthrange(year, month)[1]
    closing_date = f"{year:04d}-{month:02d}-{days_in_month:02d}"
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


async def close(args: Arguments) -> None:
    """Close ``args.period`` and open the month that follows it.

    The function discovers journals for the supplied period, keeps the ones
    named by ``args.files`` when it is set, runs the processing helper for each,
    and exits with code ``0`` on success. Any failure during journal processing
    causes the script to exit with ``1``.

    Raises:
        ValueError: When ``args.period`` is absent. The parser requires the
            positional, so only a programmatic caller can reach this.
    """

    if args.period is None:
        raise ValueError("close needs a month to close")

    folder = get_ledger_folder()

    journals = await find_monthly_journals(folder, None)
    start = parse_period_start(args.period)
    # ``parse_period_end`` returns the start of the last day which would
    # accidentally exclude the journal when passed through
    # ``filter_journals_between`` (which compares against the month's end).
    # Compute an explicit end-of-month datetime instead to ensure the entire
    # requested period is included.
    days_in_month = monthrange(start.year, start.month)[1]
    end = start.replace(
        day=days_in_month, hour=23, minute=59, second=59, microsecond=999999
    )
    journals = filter_journals_between(journals, start, end)
    if args.files is not None:
        names = frozenset(args.files)
        journals = [journal for journal in journals if Path(journal).name in names]
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
            sys.exit(1)

    sys.exit(0)


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
class Defect:
    """One boundary defect found in one monthly journal.

    Attributes:
        kind: The defect class.
        journal: Display path of the journal, relative to the repository root
            when it lies inside it.
        month: The ``YYYY-MM`` month the defect belongs to.
        detail: Human-readable specifics, such as the account and amount a
            closing left unclosed.
    """

    kind: DefectKind
    journal: str
    month: str
    detail: str


async def verify_family(
    journals: Sequence[PathLike[str]], now_month: str
) -> Sequence[Defect]:
    """Verify the boundary chain of ``journals`` and return every defect found.

    Journals are grouped by filename, since ``self.journal`` and
    ``self.alternatives.journal`` are separate chains, and each group is walked
    in month order so that a month's opening can be compared with the closing
    of the month before it in the same chain. ``now_month`` decides which
    boundaries must be present, which may be present, and which must be absent.

    A journal that cannot be read reports one ``UNREADABLE`` defect and breaks
    its chain in both directions, so the months around the gap are never
    compared with each other across it.

    The returned defects are sorted by month, journal, kind, and detail, so the
    report is stable regardless of the order the journals arrive in.
    """
    groups: dict[str, list[StdPath]] = defaultdict(list)
    for candidate in journals:
        path = StdPath(candidate)
        groups[path.name].append(path)

    defects: list[Defect] = []
    for name in sorted(groups):
        previous: Journal | None = None
        for path in sorted(groups[name], key=lambda journal: journal.parent.name):
            try:
                journal = await load_journal(path)
            except Unreadable as exc:
                defects.append(_unreadable(path, exc.detail))
                previous = None
                continue
            defects.extend(_presence_defects(journal, now_month))
            defects.extend(_ordering_defects(journal))
            linked = True
            if journal.closing is not None:
                try:
                    closed_accounts = await _closed_accounts(path)
                except Unreadable as exc:
                    defects.append(_unreadable(path, exc.detail))
                    linked = False
                else:
                    defects.extend(_assertion_defects(journal, journal.closing))
                    defects.extend(
                        _completeness_defects(journal, journal.closing, closed_accounts)
                    )
            if (
                linked
                and previous is not None
                and previous.closing is not None
                and journal.opening is not None
            ):
                defects.extend(
                    _mismatch_defects(
                        journal=journal,
                        previous_month=previous.month,
                        closing=previous.closing,
                        opening=journal.opening,
                    )
                )
            previous = journal if linked else None
    return tuple(
        sorted(
            defects,
            key=lambda defect: (
                defect.month,
                defect.journal,
                defect.kind,
                defect.detail,
            ),
        )
    )


async def _closed_accounts(path: StdPath) -> frozenset[str]:
    """Return the accounts a closing must zero, read from hledger's account types.

    Raises:
        Unreadable: When hledger fails, because guessing the types from
            account names would silently change what the verifier requires.
    """
    stdout, stderr, code = await hledger_output(path, "accounts", "--types")
    if code != 0:
        raise Unreadable(
            f"hledger accounts --types exited {code}: {first_line(stderr)}"
        )
    accounts: set[str] = set()
    for line in stdout.splitlines():
        name, separator, rest = line.partition(";")
        if not separator:
            continue
        if rest.partition("type:")[2].strip() in _CLOSED_TYPES:
            accounts.add(name.strip())
    return frozenset(accounts)


def _presence_defects(journal: Journal, now_month: str) -> Iterator[Defect]:
    """Yield defects for boundaries the month's class requires or forbids."""
    if journal.month < now_month:
        if journal.opening is None:
            yield _defect(journal, DefectKind.MISSING_OPENING, _MISSING_OPENING)
        if journal.closing is None:
            yield _defect(journal, DefectKind.MISSING_CLOSING, _MISSING_CLOSING)
    elif journal.month == now_month:
        if journal.opening is None:
            yield _defect(journal, DefectKind.MISSING_OPENING, _MISSING_OPENING)
    else:
        if journal.opening is not None:
            yield _defect(
                journal,
                DefectKind.UNEXPECTED_BOUNDARY,
                f"{OPENING_DESCRIPTION} transaction in a month after {now_month}",
            )
        if journal.closing is not None:
            yield _defect(
                journal,
                DefectKind.UNEXPECTED_BOUNDARY,
                f"{CLOSING_DESCRIPTION} transaction in a month after {now_month}",
            )


def _ordering_defects(journal: Journal) -> Iterator[Defect]:
    """Yield defects placing an existing boundary anywhere but the month's edge."""
    indexes = [transaction.tindex for transaction in journal.transactions]
    month_last_day = last_day(journal.month)
    for description in (OPENING_DESCRIPTION, CLOSING_DESCRIPTION):
        count = sum(
            1
            for transaction in journal.transactions
            if transaction.tdescription == description
        )
        if count > 1:
            yield _defect(
                journal,
                DefectKind.BOUNDARY_UNORDERED,
                f"{count} {description} transactions",
            )
    if journal.opening is not None:
        if journal.opening.tindex != min(indexes):
            yield _defect(
                journal,
                DefectKind.BOUNDARY_UNORDERED,
                f"{OPENING_DESCRIPTION} is not the first transaction",
            )
        if journal.opening.tdate != f"{journal.month}-01":
            yield _defect(
                journal,
                DefectKind.BOUNDARY_UNORDERED,
                f"{OPENING_DESCRIPTION} is dated {journal.opening.tdate}, "
                f"expected {journal.month}-01",
            )
        opening_time = _tag(journal.opening, "time")
        if opening_time != "00:00:00":
            yield _defect(
                journal,
                DefectKind.BOUNDARY_UNORDERED,
                _time_detail(OPENING_DESCRIPTION, opening_time, "00:00:00"),
            )
    if journal.closing is not None:
        if journal.closing.tindex != max(indexes):
            yield _defect(
                journal,
                DefectKind.BOUNDARY_UNORDERED,
                f"{CLOSING_DESCRIPTION} is not the last transaction",
            )
        if journal.closing.tdate != month_last_day:
            yield _defect(
                journal,
                DefectKind.BOUNDARY_UNORDERED,
                f"{CLOSING_DESCRIPTION} is dated {journal.closing.tdate}, "
                f"expected {month_last_day}",
            )
        closing_time = _tag(journal.closing, "time")
        if closing_time != "23:59:59":
            yield _defect(
                journal,
                DefectKind.BOUNDARY_UNORDERED,
                _time_detail(CLOSING_DESCRIPTION, closing_time, "23:59:59"),
            )


def _assertion_defects(journal: Journal, closing: Transaction) -> Iterator[Defect]:
    """Yield defects for closing postings that do not assert a zero balance."""
    for posting in closing.tpostings:
        if posting.paccount == _EQUITY_ACCOUNT:
            continue
        assertion = posting.pbalanceassertion
        if assertion is None:
            yield _defect(
                journal,
                DefectKind.CLOSING_NOT_ZERO,
                f"{posting.paccount}: closing posting has no balance assertion",
            )
        elif assertion.baamount.aquantity.value != 0:
            yield _defect(
                journal,
                DefectKind.CLOSING_NOT_ZERO,
                f"{posting.paccount}: closing posting asserts "
                f"{money(assertion.baamount)} instead of zero",
            )


def _completeness_defects(
    journal: Journal, closing: Transaction, closed_accounts: frozenset[str]
) -> Iterator[Defect]:
    """Yield defects for balances the closing fails to zero."""
    balances = _posting_totals(
        transaction
        for transaction in journal.transactions
        if transaction.tindex < closing.tindex
    )
    closed = _posting_totals([closing])
    for key in sorted(balances):
        account, commodity = key
        balance = balances[key]
        if balance == 0 or account not in closed_accounts:
            continue
        if key not in closed:
            yield _defect(
                journal,
                DefectKind.CLOSING_INCOMPLETE,
                f"{account}: {balance} {commodity} left unclosed",
            )
        elif closed[key] != -balance:
            yield _defect(
                journal,
                DefectKind.CLOSING_NOT_ZERO,
                f"{account}: expected {-balance} {commodity}, "
                f"found {closed[key]} {commodity}",
            )


def _mismatch_defects(
    *,
    journal: Journal,
    previous_month: str,
    closing: Transaction,
    opening: Transaction,
) -> Iterator[Defect]:
    """Yield defects where an opening does not negate the previous closing."""
    expected = _posting_totals([closing])
    actual = _posting_totals([opening])
    for key in sorted(set(expected) | set(actual)):
        account, commodity = key
        # The absent side is a zero at the present side's scale, so both halves
        # of the message read alike (``0.00 HKD``, not ``0 HKD``).
        left = expected[key] if key in expected else Decimal(0).quantize(actual[key])
        right = actual[key] if key in actual else Decimal(0).quantize(expected[key])
        if left + right == 0:
            continue
        yield _defect(
            journal,
            DefectKind.OPENING_MISMATCH,
            f"{account}: opening {journal.month} has {right} {commodity}, "
            f"closing {previous_month} has {left} {commodity}",
        )


def _posting_totals(
    transactions: Iterable[Transaction],
) -> dict[tuple[str, str], Decimal]:
    """Sum posting amounts by account and commodity.

    Postings on :data:`_EQUITY_ACCOUNT` are skipped, because its amount is
    inferred from the transaction rather than written, and hledger reports the
    inference inconsistently across commodities. A posting hledger could not
    infer an amount for carries none; it still names its account, and its
    assertion names the commodity, so it counts as present with a zero amount.
    """
    totals: dict[tuple[str, str], Decimal] = defaultdict(Decimal)
    for transaction in transactions:
        for posting in transaction.tpostings:
            if posting.paccount == _EQUITY_ACCOUNT:
                continue
            if not posting.pamount:
                assertion = posting.pbalanceassertion
                if assertion is not None:
                    totals.setdefault(
                        (posting.paccount, assertion.baamount.acommodity),
                        assertion.baamount.aquantity.zero,
                    )
                continue
            for amount in posting.pamount:
                totals[(posting.paccount, amount.acommodity)] += amount.aquantity.value
    return totals


def _tag(transaction: Transaction, key: str) -> str | None:
    """Return the value of ``transaction``'s ``key`` tag, when it carries one."""
    for name, value in transaction.ttags:
        if name == key:
            return value
    return None


def _time_detail(description: str, time: str | None, expected: str) -> str:
    """Return the detail naming a boundary's ``time`` tag and the one it needs."""
    if time is None:
        return f"{description} has no time tag, expected {expected}"
    return f"{description} has time {time}, expected {expected}"


def _defect(journal: Journal, kind: DefectKind, detail: str) -> Defect:
    """Build a defect for ``journal`` with its display path filled in."""
    return Defect(
        kind=kind,
        journal=display_path(journal.path),
        month=journal.month,
        detail=detail,
    )


def _unreadable(path: StdPath, detail: str) -> Defect:
    """Build an unreadable defect for ``path``, whose month is its directory name."""
    return Defect(
        kind=DefectKind.UNREADABLE,
        journal=display_path(path),
        month=path.parent.name,
        detail=detail,
    )


async def verify(args: Arguments) -> int:
    """Verify the selected journals and return ``1`` when any defect is reported.

    The current month is resolved first, then every monthly journal is
    discovered and narrowed by ``args.period`` and ``args.files``. Each defect
    is printed as one ``journal:month: kind: detail`` line before the exit code
    is decided, so a caller sees the whole report even when it fails.

    Raises:
        ValueError: When ``args.period`` is not a ``YYYY-MM`` month, or when a
            name in ``args.files`` matches no journal of the selected period.
            Either filter would otherwise select nothing and report a clean
            chain, so both are rejected instead.
        RuntimeError: When the current month cannot be determined.
    """
    now_month = resolve_now_month(args.now)
    period = resolve_period(args.period)
    journals = list(await find_monthly_journals(get_ledger_folder(), None))
    if period is not None:
        journals = [
            journal for journal in journals if StdPath(journal).parent.name == period
        ]
    if args.files is not None:
        names = frozenset(args.files)
        journals = [journal for journal in journals if StdPath(journal).name in names]
        unmatched = sorted(names - {StdPath(journal).name for journal in journals})
        if unmatched:
            listed = ", ".join(repr(name) for name in unmatched)
            raise ValueError(f"--files {listed} matches no journal in the period")
    info("journals:\n%s", format_journal_list(journals, max_items=8))

    defects = await verify_family(journals, now_month)
    for defect in defects:
        print(f"{defect.journal}:{defect.month}: {defect.kind}: {defect.detail}")
    info("%d boundary defect(s) for %s", len(defects), now_month)
    return 1 if defects else 0


async def main(args: Arguments) -> int:
    """Dispatch to the subcommand named by ``args.command`` and return its code.

    Returns:
        The exit code the subcommand reports. ``close`` exits through
        :func:`sys.exit` itself, so it never returns a code here.
    """

    if args.command == "close":
        await close(args)
        return 0
    return await verify(args)


def parser(parent: Callable[..., ArgumentParser] | None = None) -> ArgumentParser:
    """Construct and return the CLI ArgumentParser for the clopen script.

    The parser declares two subcommands. ``close`` takes the month to close and
    the journal filenames that restrict the run; ``verify`` takes the same two
    and ``--now``. One ``invoke`` coroutine, installed as a parser default,
    builds :class:`Arguments` from whichever subcommand ran and forwards them to
    :func:`main`.
    """

    parser = (ArgumentParser if parent is None else parent)(
        prog="clopen",
        description="close a month and open the next, or verify month boundaries",
        add_help=True,
        allow_abbrev=False,
    )

    subcommands = parser.add_subparsers(dest="command", required=True)

    close_parser = subcommands.add_parser(
        "close", help="write a closing balance and the next opening balance"
    )
    close_parser.add_argument("period", help="year-month to close (e.g. 2026-02)")
    close_parser.add_argument(
        "files",
        nargs="*",
        metavar="JOURNAL",
        help=(
            "journal filename to process, such as self.journal (not a path); "
            "every journal of the month when omitted"
        ),
    )

    verify_parser = subcommands.add_parser("verify", help="report boundary defects")
    verify_parser.add_argument(
        "period",
        nargs="?",
        help="year-month to verify (e.g. 2026-06); every month when omitted",
    )
    verify_parser.add_argument(
        "files",
        nargs="*",
        metavar="JOURNAL",
        help=(
            "journal filename to verify, such as self.journal (not a path); "
            "every journal when omitted"
        ),
    )
    verify_parser.add_argument(
        "--now",
        dest="now",
        help=(
            "current month as YYYY-MM or an ISO date, which decides whether the "
            "latest months must be closed; derived from the last commit date "
            "when omitted"
        ),
    )

    parser.set_defaults(now=None)

    @wraps(main)
    async def invoke(ns: Namespace) -> int:
        """Adapter used as ``argparse`` callback to run :func:`main`."""

        return await main(
            Arguments(
                command=ns.command,
                period=ns.period,
                files=None if not ns.files else tuple(ns.files),
                now=ns.now,
            )
        )

    parser.set_defaults(invoke=invoke)
    return parser


async def main0():
    """Parse the CLI arguments, run the subcommand, and exit with its code.

    An argument or environment error is printed as one ``error:`` line and exits
    ``1``, the same code a defect report uses, so the exit code only ever says
    whether the chain verified clean.
    """
    basicConfig(level=INFO)
    entry = parser().parse_args(sys.argv[1:])
    try:
        code = await entry.invoke(entry)
    except (ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    sys.exit(code)


def __main__():
    """Entry point for running the script directly."""
    runnify(main0, backend_options={"use_uvloop": True})()


if __name__ == "__main__":
    __main__()
