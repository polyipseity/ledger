"""Shift account balances within monthly journal files.

This script adjusts account balances found in monthly journal files by a
fixed amount. The CLI supports limiting the affected journals by inclusive
start/end datetimes. Typical invocation is:

    python -m scripts.shift <account> <amount> <currency>
"""

from argparse import ArgumentParser, Namespace
from asyncio import run
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from logging import INFO, basicConfig, info
from os import PathLike
from re import MULTILINE, NOFLAG, compile, escape
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
    make_datetime_range_filters,
    parse_amount,
    parse_period_end,
    parse_period_start,
)

__all__ = ("Arguments", "main", "parser")

_OPENING_BALANCES_REGEX = compile(r"opening balances", NOFLAG)
_CLOSING_BALANCES_REGEX = compile(r"closing balances", NOFLAG)


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
    """Command-line arguments container for `scripts.shift`.

    Attributes:
        from_datetime: Inclusive start datetime to select journals.
        to_datetime: Inclusive end datetime to select journals.
        account: Account name whose balance lines will be shifted.
        amount: Amount to add/subtract on each applicable balance line.
        currency: Currency code used in the journal lines.
    """

    from_datetime: datetime | None
    to_datetime: datetime | None
    account: str
    amount: float
    currency: str


async def main(args: Arguments) -> None:
    """Shift balances in monthly journals.

    Iterates applicable monthly journals and adjusts matching account balance
    lines by the provided amount and currency. Changes are written only when
    the journal content differs from the modified text.
    """

    folder = get_ledger_folder()

    journals = await find_monthly_journals(folder, None)
    journals = filter_journals_between(journals, args.from_datetime, args.to_datetime)
    info("journals:\n%s", format_journal_list(journals, max_items=8))

    async with JournalRunContext(Path(__file__), journals) as run:
        if run.skipped:
            info("skipped:\n%s", format_journal_list(run.skipped, max_items=8))

        async def process_journal(journal: PathLike) -> None:
            def updater(read: str) -> str:
                regex = compile(
                    rf"^( +){escape(args.account)}( +)(-?[\d ,]+(?:\.[\d ,]*)?)( +){escape(args.currency)}( *)=( *)(-?[\d ,]+(?:\.[\d ,]*)?)( +){escape(args.currency)}( *)$",
                    MULTILINE,
                )

                from_filter, to_filter = make_datetime_range_filters(
                    args.from_datetime, args.to_datetime
                )

                def process_lines(read: str) -> Iterator[str]:
                    datetime_, opening, closing = None, False, False
                    for line in read.splitlines(keepends=True):
                        try:
                            datetime_ = datetime.fromisoformat(line[:10])
                        except ValueError:
                            pass
                        else:
                            opening, closing = bool(
                                _OPENING_BALANCES_REGEX.search(line)
                            ), bool(_CLOSING_BALANCES_REGEX.search(line))
                        if (
                            datetime_ is None
                            or not from_filter(datetime_)
                            or not to_filter(datetime_)
                            or not (match := regex.match(line))
                        ):
                            yield line
                            continue
                        yield f"{match[1]}{args.account}{match[2]}{f'{{0:.{DEFAULT_AMOUNT_DECIMAL_PLACES}f}}'.format(round(parse_amount(match[3]) + args.amount * (opening - closing), DEFAULT_AMOUNT_DECIMAL_PLACES))}{match[4]}{args.currency}{match[5]}={match[6]}{f'{{0:.{DEFAULT_AMOUNT_DECIMAL_PLACES}f}}'.format(round(parse_amount(match[7]) + args.amount * (not closing), DEFAULT_AMOUNT_DECIMAL_PLACES))}{match[8]}{args.currency}{match[9]}\n"

                return "".join(process_lines(read))

            await file_update_if_changed(journal, updater)
            # Record the successful processing for this session
            run.report_success(journal)

        await gather_and_raise(*map(process_journal, run.to_process))
    exit(0)


def parser(parent: Callable[..., ArgumentParser] | None = None) -> ArgumentParser:
    """Construct and return the CLI ArgumentParser for the shift script.

    The parser sets an `invoke` coroutine as the default which calls
    :func:`main` when executed.
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
        help="datetime to start shifting (inclusive), in ISO 8601 format",
    )
    parser.add_argument(
        "-t",
        "--to",
        action="store",
        default=None,
        type=parse_period_end,
        help="datetime to stop shifting (inclusive), in ISO 8601 format",
    )
    parser.add_argument(
        "account",
        action="store",
        help="account to shift",
    )
    parser.add_argument(
        "amount",
        action="store",
        type=float,
        help="amount to shift",
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
                account=args.account,
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
