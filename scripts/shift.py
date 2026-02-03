from argparse import ArgumentParser, Namespace
from asyncio import create_task, gather, run
from calendar import monthrange
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from glob import iglob
from inspect import currentframe, getframeinfo
from logging import INFO, basicConfig, info
from re import MULTILINE, NOFLAG, compile, escape
from sys import argv, exit
from typing import final

from anyio import Path

__all__ = ("Arguments", "main", "parser")

_OPENING_BALANCES_REGEX = compile(r"opening balances", NOFLAG)
_CLOSING_BALANCES_REGEX = compile(r"closing balances", NOFLAG)
_NUMBER_OF_DIGITS = 2


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
    from_datetime: datetime | None
    to_datetime: datetime | None
    account: str
    amount: float
    currency: str


async def main(args: Arguments):
    frame = currentframe()
    if frame is None:
        raise ValueError(frame)
    folder = Path(getframeinfo(frame).filename).parent

    if (from_datetime := args.from_datetime) is None:

        def from_filter(datetime_: datetime) -> bool:
            return True

    else:

        def from_filter(datetime_: datetime) -> bool:
            return from_datetime <= datetime_

    if (to_datetime := args.to_datetime) is None:

        def to_filter(datetime_: datetime) -> bool:
            return True

    else:

        def to_filter(datetime_: datetime) -> bool:
            return datetime_ <= to_datetime

    def filter_datetime(datetime_: datetime):
        return from_filter(datetime_) and to_filter(datetime_)

    journals = await gather(
        *(
            Path(folder.parent, path).resolve(strict=True)
            for path in iglob(
                "**/*[0123456789][0123456789][0123456789][0123456789]-[0123456789][0123456789]/*.journal",
                root_dir=folder.parent,
                recursive=True,
            )
        )
    )
    journals = tuple(
        journal
        for journal in journals
        if to_filter(to_date := datetime.fromisoformat(f"{journal.parent.name}-01"))
        and from_filter(
            to_date.replace(
                day=monthrange(to_date.year, to_date.month)[1],
                hour=24 - 1,
                minute=60 - 1,
                second=60 - 1,
                microsecond=1000000 - 1,
                fold=1,
            )
        )
    )
    info(f'journals: {", ".join(map(str, journals))}')

    async def process_journal(journal: Path):
        async with await journal.open(
            mode="r+t", encoding="UTF-8", errors="strict", newline=None
        ) as file:
            read = await file.read()
            seek = create_task(file.seek(0))
            try:

                def process_lines(read: str):
                    def parse_float(float_str: str):
                        return float(float_str.replace(" ", "").replace(",", ""))

                    regex = compile(
                        rf"^( +){escape(args.account)}( +)(-?[\d ,]+(?:\.[\d ,]*)?)( +){escape(args.currency)}( *)=( *)(-?[\d ,]+(?:\.[\d ,]*)?)( +){escape(args.currency)}( *)$",
                        MULTILINE,
                    )
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
                            or not filter_datetime(datetime_)
                            or not (match := regex.match(line))
                        ):
                            yield line
                            continue
                        yield f"{match[1]}{args.account}{match[2]}{f'{{0:.{_NUMBER_OF_DIGITS}f}}'.format(round(parse_float(match[3]) + args.amount * (opening - closing), _NUMBER_OF_DIGITS))}{match[4]}{args.currency}{match[5]}={match[6]}{f'{{0:.{_NUMBER_OF_DIGITS}f}}'.format(round(parse_float(match[7]) + args.amount * (not closing), _NUMBER_OF_DIGITS))}{match[8]}{args.currency}{match[9]}\n"

                if (text := "".join(process_lines(read))) != read:
                    await seek
                    await file.write(text)
                    await file.truncate()
            finally:
                seek.cancel()

    formatErrs = tuple(
        err
        for err in await gather(*map(process_journal, journals), return_exceptions=True)
        if err
    )
    if formatErrs:
        raise BaseExceptionGroup("", formatErrs)

    exit(0)


def parser(parent: Callable[..., ArgumentParser] | None = None):
    prog = argv[0]

    def parse_from_datetime(date_string: str):
        try:
            return datetime.fromisoformat(date_string)
        except ValueError:
            with suppress(ValueError):
                return datetime.fromisoformat(f"{date_string}-01")
            with suppress(ValueError):
                return datetime.fromisoformat(f"{date_string}-01-01")
            raise

    def parse_to_datetime(date_string: str):
        try:
            return datetime.fromisoformat(date_string)
        except ValueError:
            for day in range(31, 27, -1):
                with suppress(ValueError):
                    return datetime.fromisoformat(f"{date_string}-{day}")
            for day in range(31, 27, -1):
                with suppress(ValueError):
                    return datetime.fromisoformat(f"{date_string}-12-{day}")
            raise

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
        type=parse_from_datetime,
        help="datetime to start shifting (inclusive), in ISO 8601 format",
    )
    parser.add_argument(
        "-t",
        "--to",
        action="store",
        default=None,
        type=parse_to_datetime,
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
    async def invoke(args: Namespace):
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
