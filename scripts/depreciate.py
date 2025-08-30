from calendar import monthrange
from contextlib import suppress
from datetime import datetime
from anyio import Path as _Path
from argparse import ArgumentParser as _ArgParser, Namespace as _NS
from asyncio import create_task, gather as _gather, run as _run
from dataclasses import dataclass as _dc
from functools import wraps as _wraps
from glob import iglob as _iglob
from inspect import currentframe as _curframe, getframeinfo as _frameinfo
from logging import INFO as _INFO, basicConfig as _basicConfig, info as _info
from re import NOFLAG, compile
from sys import argv as _argv, exit as _exit
from typing import Callable as _Call, final as _fin

_DEPRECIATION_REGEX = compile(r"^\d{4}-\d{2}-\d{2} +(?:[!*] +)?depreciation", NOFLAG)
_DEPRECIATION_ACCOUNT = "expenses:depreciation"
_ACCUMULATED_DEPRECIATION_ACCOUNT = "assets:accumulated depreciation"
_TIMEZONE = "UTC+08:00"
_NUMBER_OF_DIGITS = 2


@_fin
@_dc(
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
    frame = _curframe()
    if frame is None:
        raise ValueError(frame)
    folder = _Path(_frameinfo(frame).filename).parent

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

    journals = await _gather(
        *(
            _Path(folder.parent, path).resolve(strict=True)
            for path in _iglob(
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
    _info(f'journals: {", ".join(map(str, journals))}')

    async def process_journal(journal: _Path):
        journal_date = datetime.fromisoformat(f"{journal.parent.name}-01")

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
                            found = bool(_DEPRECIATION_REGEX.match(line))
                            yield line
                            continue

                        if not done and not line.strip():
                            done = True
                            yield f"    {_ACCUMULATED_DEPRECIATION_ACCOUNT}  {f'{{0:.{_NUMBER_OF_DIGITS}f}}'.format(args.amount)} {args.currency}  ; item: {args.item}\n"
                            yield line
                            continue

                        yield line

                    if not done:
                        yield f"""{journal_date.replace(
    day=monthrange(journal_date.year, journal_date.month)[1],
    hour=24 - 1,
    minute=60 - 1,
    second=60 - 1,
    microsecond=1000000 - 1,
    fold=1,
).date().isoformat()} ! depreciation  ; activity: depreciation, time: 23:59:59, timezone: {_TIMEZONE}
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
        for err in await _gather(
            *map(process_journal, journals), return_exceptions=True
        )
        if err
    )
    if formatErrs:
        raise BaseExceptionGroup("", formatErrs)

    _exit(0)


def parser(parent: _Call[..., _ArgParser] | None = None):
    prog = _argv[0]

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

    parser = (_ArgParser if parent is None else parent)(
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

    @_wraps(main)
    async def invoke(args: _NS):
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
    _basicConfig(level=_INFO)
    entry = parser().parse_args(_argv[1:])
    _run(entry.invoke(entry))
