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
from re import NOFLAG, compile
from sys import argv, exit
from typing import final

from anyio import Path

__all__ = ("Arguments", "main", "parser")

_DEPRECIATION_REGEX = compile(r"^\d{4}-\d{2}-\d{2} +(?:[!*] +)?depreciation", NOFLAG)
_DEPRECIATION_ACCOUNT = "expenses:depreciation"
_ACCUMULATED_DEPRECIATION_ACCOUNT = "assets:accumulated depreciation"
_TIMEZONE = "UTC+08:00"
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
    item: str
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
        journal_date = datetime.fromisoformat(f"{journal.parent.name}-01")
        journal_last_datetime = journal_date.replace(
            day=monthrange(journal_date.year, journal_date.month)[1],
            hour=24 - 1,
            minute=60 - 1,
            second=60 - 1,
            microsecond=1000000 - 1,
            fold=1,
        )
        journal_last_date_str = journal_last_datetime.date().isoformat()

        async with await journal.open(
            mode="r+t", encoding="UTF-8", errors="strict", newline=None
        ) as file:
            read = await file.read()
            seek = create_task(file.seek(0))
            try:

                def process_lines(read: str):
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
                            yield f"    {_ACCUMULATED_DEPRECIATION_ACCOUNT}  {f'{{0:.{_NUMBER_OF_DIGITS}f}}'.format(args.amount)} {args.currency}  ; item: {args.item}\n"
                            yield line
                            continue

                        yield line
                    else:
                        if found and not done:
                            done = True
                            yield f"    {_ACCUMULATED_DEPRECIATION_ACCOUNT}  {f'{{0:.{_NUMBER_OF_DIGITS}f}}'.format(args.amount)} {args.currency}  ; item: {args.item}\n"

                    if not done:
                        yield f"""{journal_last_date_str} ! depreciation  ; activity: depreciation, time: 23:59:59, timezone: {_TIMEZONE}
    {_DEPRECIATION_ACCOUNT}
    {_ACCUMULATED_DEPRECIATION_ACCOUNT}  {f'{{0:.{_NUMBER_OF_DIGITS}f}}'.format(args.amount)} {args.currency}  ; item: {args.item}

"""

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
        help="datetime to start depreciating (inclusive), in ISO 8601 format",
    )
    parser.add_argument(
        "-t",
        "--to",
        action="store",
        default=None,
        type=parse_to_datetime,
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
    async def invoke(args: Namespace):
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
