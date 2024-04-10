# -*- coding: UTF-8 -*-
from anyio import Path as _Path
from argparse import ArgumentParser as _ArgParser, Namespace as _NS
from asyncio import TaskGroup as _TaskGrp, gather as _gather, run as _run
from dataclasses import dataclass as _dc
from functools import wraps as _wraps
from glob import iglob as _iglob
from inspect import currentframe as _curframe, getframeinfo as _frameinfo
from logging import INFO as _INFO, basicConfig as _basicConfig, info as _info
from sys import argv as _argv, exit as _exit
from typing import Callable as _Call, final as _fin


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
    find: str
    replace: str


async def main(args: Arguments):
    frame = _curframe()
    if frame is None:
        raise ValueError(frame)
    folder = _Path(_frameinfo(frame).filename).parent

    journals = await _gather(
        *(
            _Path(folder.parent, path).resolve(strict=True)
            for path in _iglob(
                "**/*.journal",
                root_dir=folder.parent,
                recursive=True,
            )
        )
    )
    _info(f'journals: {", ".join(map(str, journals))}')

    async def replaceInJournal(journal: _Path):
        async with await journal.open(
            mode="r+t", encoding="UTF-8", errors="strict", newline=None
        ) as file:
            read = await file.read()
            async with _TaskGrp() as group:
                group.create_task(file.seek(0))
                text = read.replace(args.find, args.replace)
            if text != read:
                await file.write(text)
                await file.truncate()

    formatErrs = tuple(
        err
        for err in await _gather(
            *map(replaceInJournal, journals), return_exceptions=True
        )
        if err
    )
    if formatErrs:
        raise BaseExceptionGroup("", formatErrs)

    _exit(0)


def parser(parent: _Call[..., _ArgParser] | None = None):
    prog = _argv[0]

    parser = (_ArgParser if parent is None else parent)(
        prog=prog,
        description="replace in journals",
        add_help=True,
        allow_abbrev=False,
        exit_on_error=False,
    )
    parser.add_argument(
        "find",
        action="store",
        help="text to find",
    )
    parser.add_argument(
        "replace",
        action="store",
        help="replacement text",
    )

    @_wraps(main)
    async def invoke(ns: _NS):
        await main(Arguments(find=ns.find, replace=ns.replace))

    parser.set_defaults(invoke=invoke)
    return parser


if __name__ == "__main__":
    _basicConfig(level=_INFO)
    entry = parser().parse_args(_argv[1:])
    _run(entry.invoke(entry))
