"""Add depreciation entries to monthly journals.

This script inserts per-item depreciation lines into the end of monthly
journals within the selected date range. It ensures accumulated depreciation
entries are present and appends a new depreciation transaction if necessary.
"""

from argparse import ArgumentParser, Namespace
from asyncio import run
from calendar import monthrange
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from logging import INFO, basicConfig, info
from os import PathLike
from re import NOFLAG, compile
from sys import argv, exit
from typing import final

from anyio import Path

from .util.cache import JournalRunContext
from .util.concurrency import gather_and_raise
from .util.files import file_update_if_changed, get_ledger_folder
from .util.journals import (
    DEFAULT_AMOUNT_DECIMAL_PLACES,
    filter_journals_between,
    find_monthly_journals,
    format_journal_list,
    parse_period_end,
    parse_period_start,
)

__all__ = ("Arguments", "main", "parser")

_DEPRECIATION_REGEX = compile(r"^\d{4}-\d{2}-\d{2} +(?:[!*] +)?depreciation", NOFLAG)
_DEPRECIATION_ACCOUNT = "expenses:depreciation"
_ACCUMULATED_DEPRECIATION_ACCOUNT = "assets:accumulated depreciation"
_TIMEZONE = "UTC+08:00"


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
    """CLI arguments container for `scripts.depreciate`.

    Attributes:
        from_datetime: Inclusive start datetime to select journals.
        to_datetime: Inclusive end datetime to select journals.
        item: The item identifier to attribute depreciation to (used in comment).
        amount: Depreciation amount to record per journal.
        currency: Currency code used in the journal entries.
    """

    from_datetime: datetime | None
    to_datetime: datetime | None
    item: str
    amount: float
    currency: str


async def main(args: Arguments) -> None:
    """Insert depreciation entries into monthly journals.

    Processes monthly journals in the supplied inclusive date range and
    ensures an accumulated depreciation posting exists for each period. If a
    target journal does not contain a depreciation transaction, a new one is
    appended.
    """

    folder = get_ledger_folder()

    journals = await find_monthly_journals(folder, None)
    journals = filter_journals_between(journals, args.from_datetime, args.to_datetime)
    info("journals:\n%s", format_journal_list(journals, max_items=8))

    async with JournalRunContext(Path(__file__), journals) as run:
        if run.skipped:
            info("skipped:\n%s", format_journal_list(run.skipped, max_items=8))

        async def process_journal(journal: PathLike) -> None:
            p = Path(journal)
            journal_date = datetime.fromisoformat(f"{p.parent.name}-01")
            journal_last_datetime = journal_date.replace(
                day=monthrange(journal_date.year, journal_date.month)[1],
                hour=23,
                minute=59,
                second=59,
                microsecond=999999,
                fold=1,
            )
            journal_last_date_str = journal_last_datetime.date().isoformat()

            def updater(read: str) -> str:
                def process_lines(read: str) -> Iterator[str]:
                    found, done = False, False
                    for line in read.splitlines(keepends=True):
                        if not found:
                            found = bool(
                                _DEPRECIATION_REGEX.match(line)
                            ) and line.startswith(journal_last_date_str)
                            yield line
                            continue

                        if not done and not line.strip():
                            done = True
                            yield f"    {_ACCUMULATED_DEPRECIATION_ACCOUNT}  {f'{{0:.{DEFAULT_AMOUNT_DECIMAL_PLACES}f}}'.format(args.amount)} {args.currency}  ; item: {args.item}\n"
                            yield line
                            continue

                        yield line
                    else:
                        if found and not done:
                            done = True
                            yield f"    {_ACCUMULATED_DEPRECIATION_ACCOUNT}  {f'{{0:.{DEFAULT_AMOUNT_DECIMAL_PLACES}f}}'.format(args.amount)} {args.currency}  ; item: {args.item}\n"

                    if not done:
                        yield f"""{journal_last_date_str} ! depreciation  ; activity: depreciation, time: 23:59:59, timezone: {_TIMEZONE}
    {_DEPRECIATION_ACCOUNT}
    {_ACCUMULATED_DEPRECIATION_ACCOUNT}  {f'{{0:.{DEFAULT_AMOUNT_DECIMAL_PLACES}f}}'.format(args.amount)} {args.currency}  ; item: {args.item}

"""

                return "".join(process_lines(read))

            await file_update_if_changed(journal, updater)
            # Record the successful processing for this session
            run.report_success(journal)

        await gather_and_raise(*map(process_journal, run.to_process))
    exit(0)


def parser(parent: Callable[..., ArgumentParser] | None = None) -> ArgumentParser:
    """Build and return the CLI ArgumentParser for the depreciation script.

    The parser accepts start/end period options and positional arguments
    for item, amount and currency. It sets an `invoke` coroutine default
    that runs :func:`main`.
    """

    prog = argv[0]

    parser = (ArgumentParser if parent is None else parent)(
        prog=prog,
        description="shift an account balance",
        add_help=True,
        allow_abbrev=False,
        exit_on_error=False,
    )
    parser.add_argument(
        "-f",
        "--from",
        action="store",
        default=None,
        type=parse_period_start,
        help="datetime to start depreciating (inclusive), in ISO 8601 format",
    )
    parser.add_argument(
        "-t",
        "--to",
        action="store",
        default=None,
        type=parse_period_end,
        help="datetime to stop depreciating (inclusive), in ISO 8601 format",
    )
    parser.add_argument(
        "item",
        action="store",
        help="item to depreciate",
    )
    parser.add_argument(
        "amount",
        action="store",
        type=float,
        help="amount to depreciate per journal",
    )
    parser.add_argument(
        "currency",
        action="store",
        help="type of currency",
    )

    @wraps(main)
    async def invoke(args: Namespace) -> None:
        await main(
            Arguments(
                from_datetime=getattr(args, "from"),
                to_datetime=args.to,
                item=args.item,
                amount=args.amount,
                currency=args.currency,
            )
        )

    parser.set_defaults(invoke=invoke)
    return parser


if __name__ == "__main__":
    basicConfig(level=INFO)
    entry = parser().parse_args(argv[1:])
    run(entry.invoke(entry))
