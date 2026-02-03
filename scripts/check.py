from argparse import ArgumentParser, Namespace
from asyncio import BoundedSemaphore, create_subprocess_exec, gather, run
from asyncio.subprocess import DEVNULL, PIPE
from dataclasses import dataclass
from functools import wraps
from glob import iglob
from inspect import currentframe, getframeinfo
from logging import INFO, basicConfig, info
from os import cpu_count
from shutil import which
from sys import argv, exit
from typing import Callable, final

from anyio import Path

__all__ = ("Arguments", "main", "parser")

_SUBPROCESS_SEMAPHORE = BoundedSemaphore(cpu_count() or 4)


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
    files: list[str] | None = None


async def main(args: Arguments):
    frame = currentframe()
    if frame is None:
        raise ValueError(frame)
    folder = Path(getframeinfo(frame).filename).parent

    if args.files:
        journals = await gather(
            *(Path(path).resolve(strict=True) for path in args.files)
        )
    else:
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
    info(f'journals: {", ".join(map(str, journals))}')

    hledger_prog = which("hledger")
    if hledger_prog is None:
        raise FileNotFoundError(hledger_prog)

    async def checkJournal(journal: Path):
        async with _SUBPROCESS_SEMAPHORE:
            proc = await create_subprocess_exec(
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
                stdin=DEVNULL,
                stdout=PIPE,
                stderr=PIPE,
            )
            _stdout, stderr = (
                std.decode().replace("\r\n", "\n") for std in await proc.communicate()
            )
            if await proc.wait():
                raise ChildProcessError(proc.returncode, stderr)

    errors = tuple(
        err
        for err in await gather(*map(checkJournal, journals), return_exceptions=True)
        if err
    )
    if errors:
        raise BaseExceptionGroup("", errors)

    exit(0)


def parser(parent: Callable[..., ArgumentParser] | None = None):
    prog = argv[0]

    parser = (ArgumentParser if parent is None else parent)(
        prog=prog,
        description="check journals",
        add_help=True,
        allow_abbrev=False,
        exit_on_error=False,
    )

    @wraps(main)
    async def invoke(ns: Namespace):
        await main(Arguments(files=getattr(ns, "files", None)))

    parser.add_argument(
        "files",
        nargs="*",
        help="Optional list of journal files to check",
    )

    parser.set_defaults(invoke=invoke)
    return parser


if __name__ == "__main__":
    basicConfig(level=INFO)
    entry = parser().parse_args(argv[1:])
    # maintain compatibility with existing invocation pattern
    run(entry.invoke(entry))
