from anyio import Path as _Path
from argparse import ArgumentParser as _ArgParser, Namespace as _NS
from asyncio import (
    BoundedSemaphore as _BSemp,
    create_subprocess_exec as _new_sproc,
    gather as _gather,
    run as _run,
)
from asyncio.subprocess import DEVNULL as _DEVNULL, PIPE as _PIPE
from dataclasses import dataclass as _dc
from functools import wraps as _wraps
from glob import iglob as _iglob
from inspect import currentframe as _curframe, getframeinfo as _frameinfo
from logging import INFO as _INFO, basicConfig as _basicConfig, info as _info
from os import cpu_count as _cpu_c
from shutil import which as _which
from sys import argv as _argv, exit as _exit
from typing import Callable as _Call, final as _fin

_SUBPROCESS_SEMAPHORE = _BSemp(_cpu_c() or 4)


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
                "**/*[0123456789][0123456789][0123456789][0123456789]-[0123456789][0123456789]/*.journal",
                root_dir=folder.parent,
                recursive=True,
            )
        )
    )
    _info(f'journals: {", ".join(map(str, journals))}')

    hledger_prog = _which("hledger")
    if hledger_prog is None:
        raise FileNotFoundError(hledger_prog)

    async def checkJournal(journal: _Path):
        async with _SUBPROCESS_SEMAPHORE:
            proc = await _new_sproc(
                hledger_prog,
                "--file",
                journal,
                "--strict",
                "check",
                "accounts",
                "assertions",
                "autobalanced",
                "balanced",
                "commodities",
                "ordereddates",
                "parseable",
                "payees",
                "tags",
                stdin=_DEVNULL,
                stdout=_PIPE,
                stderr=_PIPE,
            )
            _stdout, stderr = (
                std.decode().replace("\r\n", "\n") for std in await proc.communicate()
            )
        if proc.returncode:
            raise ChildProcessError(proc.returncode, stderr)

    errors = tuple(
        err
        for err in await _gather(*map(checkJournal, journals), return_exceptions=True)
        if err
    )
    if errors:
        raise BaseExceptionGroup("", errors)

    _exit(0)


def parser(parent: _Call[..., _ArgParser] | None = None):
    prog = _argv[0]

    parser = (_ArgParser if parent is None else parent)(
        prog=prog,
        description="check journals",
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
