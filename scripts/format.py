# -*- coding: UTF-8 -*-
from anyio import Path as _Path
from argparse import ArgumentParser as _ArgParser, Namespace as _NS
from asyncio import (
    TaskGroup as TaskGrp,
    create_subprocess_exec as _new_sproc,
    gather as _gather,
    run as _run,
)
from asyncio.subprocess import PIPE as _PIPE
from dataclasses import dataclass as _dc
from functools import wraps as _wraps
from glob import iglob as _iglob
from inspect import currentframe as _curframe, getframeinfo as _frameinfo
from logging import INFO as _INFO, basicConfig as _basicConfig, info as _info
from shutil import which as _which
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
    pass


async def main(_: Arguments):
    frame = _curframe()
    if frame is None:
        raise ValueError(frame)
    folder = _Path(_frameinfo(frame).filename).parent

    journals = await _gather(
        *(
            _Path(folder.parent, path).resolve(strict=True)
            for path in _iglob(
                "**/*[0123456789][0123456789][0123456789][0123456789]-[0123456789][0123456789].journal",
                root_dir=folder.parent,
                recursive=True,
            )
        )
    )
    _info(f'journals: {", ".join(map(str, journals))}')

    hledger_prog = _which("hledger")
    if hledger_prog is None:
        raise FileNotFoundError(hledger_prog)

    async def formatJournal(journal: _Path):
        proc = await _new_sproc(
            hledger_prog, "--strict", "--file", journal, "print", stdout=_PIPE
        )
        stdout, _ = await proc.communicate()
        stdout = stdout.decode().replace("\r\n", "\n")
        if proc.returncode:
            raise ChildProcessError(proc.returncode)

        async with await journal.open(
            mode="r+t", encoding="UTF-8", errors="strict", newline=None
        ) as file:
            lines = await file.readlines()
            async with TaskGrp() as group:
                group.create_task(file.seek(0))
                header = "\n".join(
                    line for line in lines if line.startswith("include ")
                )
                text = f"""{header}
{stdout.strip()}
"""
            await file.write(text)
            await file.truncate()

    await _gather(*map(formatJournal, journals))

    _exit(0)


def parser(parent: _Call[..., _ArgParser] | None = None):
    prog = _argv[0]

    parser = (_ArgParser if parent is None else parent)(
        prog=prog,
        description="reformat journals",
        add_help=True,
        allow_abbrev=False,
        exit_on_error=False,
    )

    @_wraps(main)
    async def invoke(_: _NS):
        await main(Arguments())

    parser.set_defaults(invoke=invoke)
    return parser


if __name__ == "__main__":
    _basicConfig(level=_INFO)
    entry = parser().parse_args(_argv[1:])
    _run(entry.invoke(entry))
