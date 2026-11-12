"""Verify the monthly opening and closing balance chain of the ledger journals.

``hledger check`` passes on a ledger whose monthly chain is broken, because a
month that never received its ``closing balances`` transaction simply lets the
balances roll forward: no assertion is violated, so nothing else notices. This
script is the tool that does notice. It reads every monthly journal,
classifies each one against the current month, and reports every boundary
defect as one ``journal:month: kind: detail`` line.

Usage example:

    python -m scripts.clopen_verify
    python -m scripts.clopen_verify --now 2026-11
    python -m scripts.clopen_verify --period 2026-06 --files self.journal

Months before the current month need both boundaries, the current month needs
only its opening, and later months must carry neither. On top of that presence
rule, the boundaries are checked in content: the opening must sit first in the
month and the closing last, every closing posting must assert a zero balance,
every asset and liability account with a non-zero balance must be zeroed by the
closing, and each month's opening must negate the closing of the month before
it in the same journal family.

The script is read-only by construction: it never writes a journal, never
touches the run cache, and never repairs what it reports.

The current month comes from the committer date of the last commit
(``git log -1 --format=%cI``) rather than the author date, because a rebase,
amend, or cherry-pick advances the committer date, so it tracks when the record
actually landed, whereas an author date can survive a rebase for months.
"""

from argparse import ArgumentParser, Namespace
from calendar import monthrange
from collections import defaultdict
from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from functools import wraps
from logging import INFO, basicConfig, info
from os import PathLike, fspath
from pathlib import Path as _StdPath
from re import Pattern, compile
from subprocess import CalledProcessError, run
from sys import argv, exit
from typing import final

from asyncer import runnify
from pydantic import BaseModel, ConfigDict, RootModel, ValidationError

from .utils.files import get_ledger_folder, get_script_folder
from .utils.journals import find_monthly_journals, format_journal_list, run_hledger

"""Public symbols exported by this module."""
__all__ = (
    "Arguments",
    "Defect",
    "DefectKind",
    "main",
    "main0",
    "parser",
    "resolve_now_month",
    "verify_family",
)

"""Description of the transaction that carries a month's opening balances."""
_OPENING_DESCRIPTION = "opening balances"
"""Description of the transaction that carries a month's closing balances."""
_CLOSING_DESCRIPTION = "closing balances"
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
"""Pattern an explicit ``--now`` value must start with."""
_MONTH_PATTERN: Pattern[str] = compile("[0-9]{4}-[0-9]{2}")
"""Detail reported when a month that requires an opening balance has none."""
_MISSING_OPENING = "no opening balances transaction"
"""Detail reported when a month that requires a closing balance has none."""
_MISSING_CLOSING = "no closing balances transaction"


class DefectKind(StrEnum):
    """Kind of monthly boundary defect the verifier reports."""

    MISSING_OPENING = "missing_opening"
    MISSING_CLOSING = "missing_closing"
    UNEXPECTED_BOUNDARY = "unexpected_boundary"
    CLOSING_NOT_ZERO = "closing_not_zero"
    CLOSING_INCOMPLETE = "closing_incomplete"
    OPENING_MISMATCH = "opening_mismatch"
    BOUNDARY_UNORDERED = "boundary_unordered"
    UNREADABLE = "unreadable"


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
    """Command-line arguments container for :mod:`scripts.clopen_verify`.

    Attributes:
        period: A ``YYYY-MM`` string; when given, only journals inside that
            month directory are verified. ``None`` verifies every month.
        files: Journal filenames such as ``"self.journal"``; when given, only
            journals carrying one of those names are verified. ``None``
            verifies every journal filename.
        now: A ``YYYY-MM`` string or an ISO date whose first seven characters
            name the current month; ``None`` derives it from the committer date
            of the last commit.
    """

    period: str | None = None
    files: Sequence[str] | None = None
    now: str | None = None


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


def resolve_now_month(explicit: str | None) -> str:
    """Return the ``YYYY-MM`` month separating closed months from future ones.

    An explicit value wins after checking that it starts with a four-digit
    year, a dash, and a two-digit month, and is truncated to those seven
    characters. Without one, the committer date of the last commit supplies the
    month, read from the repository root.

    Raises:
        ValueError: When ``explicit`` does not start with a ``YYYY-MM`` prefix.
        RuntimeError: When git is missing, exits non-zero, or prints nothing,
            since there is then no month to classify the journals against.
    """
    if explicit is not None:
        month = explicit[:7]
        if _MONTH_PATTERN.fullmatch(month) is None:
            raise ValueError(f"not a year-month prefix: {explicit!r}")
        return month

    root = fspath(get_script_folder(depth=1))
    try:
        completed = run(
            ("git", "log", "-1", "--format=%cI"),
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise RuntimeError(
            f"cannot determine the current month: git failed to start in {root}: {exc}"
        ) from exc
    if completed.returncode != 0:
        raise RuntimeError(
            "cannot determine the current month: "
            f"git log exited {completed.returncode}: {_first_line(completed.stderr)}"
        )
    month = completed.stdout.strip()[:7]
    if not month:
        raise RuntimeError(
            f"cannot determine the current month: git log printed no commit date in {root}"
        )
    return month


async def verify_family(
    journals: Sequence[PathLike[str]], now_month: str
) -> Sequence[Defect]:
    """Verify the boundary chain of ``journals`` and return every defect found.

    Journals are grouped by filename, since ``self.journal`` and
    ``self.alternatives.journal`` are separate chains, and each group is walked
    in month order so that a month's opening can be compared with the closing
    of the month before it in the same chain. ``now_month`` decides which
    boundaries must be present, which may be present, and which must be absent.

    The returned defects are sorted by month, journal, kind, and detail, so the
    report is stable regardless of the order the journals arrive in.
    """
    groups: dict[str, list[_StdPath]] = defaultdict(list)
    for candidate in journals:
        path = _StdPath(candidate)
        groups[path.name].append(path)

    defects: list[Defect] = []
    for name in sorted(groups):
        chain: list[_Journal] = []
        for path in sorted(groups[name], key=lambda journal: journal.parent.name):
            try:
                journal = await _load_journal(path)
            except _Unreadable as exc:
                defects.append(_unreadable(path, exc.detail))
                continue
            defects.extend(_presence_defects(journal, now_month))
            defects.extend(_ordering_defects(journal))
            if journal.closing is not None:
                try:
                    closed_accounts = await _closed_accounts(path)
                except _Unreadable as exc:
                    defects.append(_unreadable(path, exc.detail))
                    chain.append(journal)
                    continue
                defects.extend(_assertion_defects(journal, journal.closing))
                defects.extend(
                    _completeness_defects(journal, journal.closing, closed_accounts)
                )
            chain.append(journal)
        for previous, current in zip(chain, chain[1:]):
            if previous.closing is None or current.opening is None:
                continue
            defects.extend(
                _mismatch_defects(
                    journal=current,
                    previous_month=previous.month,
                    closing=previous.closing,
                    opening=current.opening,
                )
            )
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


@final
class _Unreadable(Exception):
    """A journal whose contents the verifier could not read.

    Attributes:
        detail: The reason, ready to become an :attr:`DefectKind.UNREADABLE`
            defect detail.
    """

    detail: str

    def __init__(self, detail: str) -> None:
        """Store ``detail`` as the reason the journal could not be read."""
        super().__init__(detail)
        self.detail = detail


class _Quantity(BaseModel):
    """Exact decimal quantity as hledger reports it."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    decimalMantissa: int
    decimalPlaces: int

    @property
    def value(self) -> Decimal:
        """Return the quantity as an exact decimal."""
        return Decimal(self.decimalMantissa).scaleb(-self.decimalPlaces)

    @property
    def zero(self) -> Decimal:
        """Return zero at the same scale as the quantity, for reporting."""
        return Decimal(0).scaleb(-self.decimalPlaces)


class _Amount(BaseModel):
    """One commodity amount inside a posting or a balance assertion."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    acommodity: str
    aquantity: _Quantity


class _BalanceAssertion(BaseModel):
    """Balance assertion attached to a closing posting."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    baamount: _Amount


class _Posting(BaseModel):
    """One posting of a transaction."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    paccount: str
    pamount: list[_Amount]
    pbalanceassertion: _BalanceAssertion | None = None


class _Transaction(BaseModel):
    """One transaction as ``hledger print -O json`` reports it.

    ``tindex`` is hledger's journal-order index, the only reliable ordering
    signal: the time of day lives in the ``time`` tag, not in ``tdate``.
    """

    model_config = ConfigDict(extra="ignore", frozen=True)

    tdate: str
    tdescription: str
    tindex: int
    tpostings: list[_Posting]
    ttags: list[tuple[str, str]]


class _JournalDocument(RootModel[list[_Transaction]]):
    """Top-level JSON document of one journal, holding its transactions."""


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
class _Journal:
    """A monthly journal reduced to what the boundary checks need.

    Attributes:
        path: The journal file on disk.
        month: The ``YYYY-MM`` month taken from the journal's directory name.
        transactions: Every transaction, in journal order.
        opening: The opening balance transaction, when the month has one.
        closing: The closing balance transaction, when the month has one.
    """

    path: _StdPath
    month: str
    transactions: Sequence[_Transaction]
    opening: _Transaction | None
    closing: _Transaction | None


async def _hledger_output(journal: _StdPath, *args: str) -> tuple[str, str, int]:
    """Run hledger on ``journal`` and return its output, error text, and exit code.

    ``run_hledger`` is asked not to raise, but anyio's ``run_process`` raises
    ``CalledProcessError`` before that option is consulted, so a non-zero exit
    arrives here as an exception and is flattened back into the same tuple.
    Either way a broken journal must become an ``UNREADABLE`` defect rather than
    a crash.
    """
    try:
        return await run_hledger(
            journal,
            *args,
            strict=False,
            raise_on_error=False,
            log_on_error=False,
        )
    except CalledProcessError as exc:
        stdout = exc.stdout if isinstance(exc.stdout, bytes) else b""
        stderr = exc.stderr if isinstance(exc.stderr, bytes) else b""
        return stdout.decode(), stderr.decode(), exc.returncode


async def _load_journal(path: _StdPath) -> _Journal:
    """Return ``path`` parsed into boundary data.

    hledger runs without ``--strict`` because account declarations play no part
    in boundary arithmetic, so that a journal missing declarations still counts.

    Raises:
        _Unreadable: When hledger fails, prints nothing, or prints something
            that is not a hledger journal document.
    """
    stdout, stderr, code = await _hledger_output(path, "print", "-O", "json")
    if code != 0:
        raise _Unreadable(f"hledger print exited {code}: {_first_line(stderr)}")
    if not stdout.strip():
        raise _Unreadable("hledger print produced no output")
    try:
        document = _JournalDocument.model_validate_json(stdout)
    except ValidationError as exc:
        raise _Unreadable(
            f"hledger print produced an unexpected document: {_first_line(str(exc))}"
        ) from exc
    transactions = document.root
    return _Journal(
        path=path,
        month=path.parent.name,
        transactions=transactions,
        opening=_boundary(transactions, _OPENING_DESCRIPTION, last=False),
        closing=_boundary(transactions, _CLOSING_DESCRIPTION, last=True),
    )


async def _closed_accounts(path: _StdPath) -> frozenset[str]:
    """Return the accounts a closing must zero, read from hledger's account types.

    Raises:
        _Unreadable: When hledger fails, because guessing the types from
            account names would silently change what the verifier requires.
    """
    stdout, stderr, code = await _hledger_output(path, "accounts", "--types")
    if code != 0:
        raise _Unreadable(
            f"hledger accounts --types exited {code}: {_first_line(stderr)}"
        )
    accounts: set[str] = set()
    for line in stdout.splitlines():
        name, separator, rest = line.partition(";")
        if not separator:
            continue
        if rest.partition("type:")[2].strip() in _CLOSED_TYPES:
            accounts.add(name.strip())
    return frozenset(accounts)


def _boundary(
    transactions: Sequence[_Transaction], description: str, *, last: bool
) -> _Transaction | None:
    """Return the boundary transaction described by ``description``, if any."""
    matches = [
        transaction
        for transaction in transactions
        if transaction.tdescription == description
    ]
    if not matches:
        return None
    return matches[-1] if last else matches[0]


def _presence_defects(journal: _Journal, now_month: str) -> Iterator[Defect]:
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
                f"{_OPENING_DESCRIPTION} transaction in a month after {now_month}",
            )
        if journal.closing is not None:
            yield _defect(
                journal,
                DefectKind.UNEXPECTED_BOUNDARY,
                f"{_CLOSING_DESCRIPTION} transaction in a month after {now_month}",
            )


def _ordering_defects(journal: _Journal) -> Iterator[Defect]:
    """Yield defects placing an existing boundary anywhere but the month's edge."""
    indexes = [transaction.tindex for transaction in journal.transactions]
    year, month = journal.month.split("-")
    last_day = f"{journal.month}-{monthrange(int(year), int(month))[1]:02d}"
    if journal.opening is not None:
        if journal.opening.tindex != min(indexes):
            yield _defect(
                journal,
                DefectKind.BOUNDARY_UNORDERED,
                f"{_OPENING_DESCRIPTION} is not the first transaction",
            )
        if journal.opening.tdate != f"{journal.month}-01":
            yield _defect(
                journal,
                DefectKind.BOUNDARY_UNORDERED,
                f"{_OPENING_DESCRIPTION} is dated {journal.opening.tdate}, "
                f"expected {journal.month}-01",
            )
        opening_time = _tag(journal.opening, "time")
        if opening_time != "00:00:00":
            yield _defect(
                journal,
                DefectKind.BOUNDARY_UNORDERED,
                _time_detail(_OPENING_DESCRIPTION, opening_time, "00:00:00"),
            )
    if journal.closing is not None:
        if journal.closing.tindex != max(indexes):
            yield _defect(
                journal,
                DefectKind.BOUNDARY_UNORDERED,
                f"{_CLOSING_DESCRIPTION} is not the last transaction",
            )
        if journal.closing.tdate != last_day:
            yield _defect(
                journal,
                DefectKind.BOUNDARY_UNORDERED,
                f"{_CLOSING_DESCRIPTION} is dated {journal.closing.tdate}, "
                f"expected {last_day}",
            )
        closing_time = _tag(journal.closing, "time")
        if closing_time != "23:59:59":
            yield _defect(
                journal,
                DefectKind.BOUNDARY_UNORDERED,
                _time_detail(_CLOSING_DESCRIPTION, closing_time, "23:59:59"),
            )


def _assertion_defects(journal: _Journal, closing: _Transaction) -> Iterator[Defect]:
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
                f"{_money(assertion.baamount)} instead of zero",
            )


def _completeness_defects(
    journal: _Journal, closing: _Transaction, closed_accounts: frozenset[str]
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
    journal: _Journal,
    previous_month: str,
    closing: _Transaction,
    opening: _Transaction,
) -> Iterator[Defect]:
    """Yield defects where an opening does not negate the previous closing."""
    expected = _posting_totals([closing])
    actual = _posting_totals([opening])
    for key in sorted(set(expected) | set(actual)):
        account, commodity = key
        left = expected.get(key, Decimal(0))
        right = actual.get(key, Decimal(0))
        if left + right == 0:
            continue
        yield _defect(
            journal,
            DefectKind.OPENING_MISMATCH,
            f"{account}: opening {journal.month} has {right} {commodity}, "
            f"closing {previous_month} has {left} {commodity}",
        )


def _posting_totals(
    transactions: Iterable[_Transaction],
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


def _tag(transaction: _Transaction, key: str) -> str | None:
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


def _money(amount: _Amount) -> str:
    """Return ``amount`` as an exact quantity followed by its commodity."""
    return f"{amount.aquantity.value} {amount.acommodity}"


def _first_line(text: str) -> str:
    """Return the first non-empty line of ``text``, or a placeholder when empty."""
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return "(no output)"


def _defect(journal: _Journal, kind: DefectKind, detail: str) -> Defect:
    """Build a defect for ``journal`` with its display path filled in."""
    return Defect(
        kind=kind,
        journal=_display_path(journal.path),
        month=journal.month,
        detail=detail,
    )


def _unreadable(path: _StdPath, detail: str) -> Defect:
    """Build an unreadable defect for ``path``, whose month is its directory name."""
    return Defect(
        kind=DefectKind.UNREADABLE,
        journal=_display_path(path),
        month=path.parent.name,
        detail=detail,
    )


def _display_path(path: _StdPath) -> str:
    """Return ``path`` relative to the repository root when it lies inside it."""
    try:
        return fspath(path.relative_to(fspath(get_script_folder(depth=1))))
    except ValueError:
        return fspath(path)


async def main(args: Arguments) -> None:
    """Verify the selected journals and exit ``1`` when any defect is reported.

    The current month is resolved first, then every monthly journal is
    discovered and narrowed by ``args.period`` and ``args.files``. Each defect
    is printed as one ``journal:month: kind: detail`` line before the exit code
    is decided, so a caller sees the whole report even when it fails.
    """
    now_month = resolve_now_month(args.now)
    journals = list(await find_monthly_journals(get_ledger_folder(), None))
    if args.period is not None:
        journals = [
            journal
            for journal in journals
            if _StdPath(journal).parent.name == args.period
        ]
    if args.files is not None:
        names = frozenset(args.files)
        journals = [journal for journal in journals if _StdPath(journal).name in names]
    info("journals:\n%s", format_journal_list(journals, max_items=8))

    defects = await verify_family(journals, now_month)
    for defect in defects:
        print(f"{defect.journal}:{defect.month}: {defect.kind}: {defect.detail}")
    info("%d boundary defect(s) for %s", len(defects), now_month)
    exit(1 if defects else 0)


def parser(parent: Callable[..., ArgumentParser] | None = None) -> ArgumentParser:
    """Construct and return the CLI ArgumentParser for the verifier.

    The parser adds ``--period``, a repeatable ``--files``, and ``--now``, then
    installs an ``invoke`` coroutine that builds :class:`Arguments` and forwards
    them to :func:`main`.
    """
    prog = argv[0]

    parser = (ArgumentParser if parent is None else parent)(
        prog=prog,
        description="verify the monthly closing and opening balance chain",
        add_help=True,
        allow_abbrev=False,
        exit_on_error=False,
    )

    parser.add_argument(
        "--period",
        help="month to verify (e.g. 2026-06); every month when omitted",
    )
    parser.add_argument(
        "--files",
        action="append",
        metavar="JOURNAL",
        help=(
            "journal filename to verify, such as self.journal (not a path); "
            "repeat to name more than one"
        ),
    )
    parser.add_argument(
        "--now",
        help=(
            "current month as YYYY-MM or an ISO date, which decides whether the "
            "latest months must be closed; derived from the last commit date "
            "when omitted"
        ),
    )

    @wraps(main)
    async def invoke(ns: Namespace) -> None:
        """Adapter used as the ``argparse`` callback to run :func:`main`."""

        await main(
            Arguments(
                period=ns.period,
                files=None if ns.files is None else tuple(ns.files),
                now=ns.now,
            )
        )

    parser.set_defaults(invoke=invoke)
    return parser


async def main0() -> None:
    """Entry point for running the script directly. Parses CLI arguments and invokes main()."""
    basicConfig(level=INFO)
    entry = parser().parse_args(argv[1:])
    await entry.invoke(entry)


def __main__() -> None:
    """Entry point for running the script directly."""
    runnify(main0, backend_options={"use_uvloop": True})()


if __name__ == "__main__":
    __main__()
