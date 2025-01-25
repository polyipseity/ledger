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
from re import MULTILINE, NOFLAG, compile, escape
from sys import argv as _argv, exit as _exit
from typing import Callable as _Call, final as _fin

_OPENING_BALANCES_REGEX = compile(r"opening balances", NOFLAG)
_CLOSING_BALANCES_REGEX = compile(r"closing balances", NOFLAG)
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
    account: str
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
        if filter_datetime(datetime.fromisoformat(f"{journal.parent.name}-01"))
    )
    _info(f'journals: {", ".join(map(str, journals))}')

    async def process_journal(journal: _Path):
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

    @_wraps(main)
    async def invoke(args: _NS):
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
    _basicConfig(level=_INFO)
    entry = parser().parse_args(_argv[1:])
    _run(entry.invoke(entry))
