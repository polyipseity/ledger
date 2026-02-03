from argparse import ArgumentParser, Namespace
from asyncio import create_task, gather, run
from dataclasses import dataclass
from functools import wraps
from glob import iglob
from inspect import currentframe, getframeinfo
from logging import INFO, basicConfig, info
from sys import argv, exit
from typing import Callable, final

from anyio import Path

__all__ = ("Arguments", "main", "parser")


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
    find: str
    replace: str


async def main(args: Arguments):
    frame = currentframe()
    if frame is None:
        raise ValueError(frame)
    folder = Path(getframeinfo(frame).filename).parent

    journals = await gather(
        *(
            Path(folder.parent, path).resolve(strict=True)
            for path in iglob(
                "**/*.journal",
                root_dir=folder.parent,
                recursive=True,
            )
        )
    )
    info(f'journals: {", ".join(map(str, journals))}')

    async def replaceInJournal(journal: Path):
        async with await journal.open(
            mode="r+t", encoding="UTF-8", errors="strict", newline=None
        ) as file:
            read = await file.read()
            seek = create_task(file.seek(0))
            try:
                if (text := read.replace(args.find, args.replace)) != read:
                    await seek
                    await file.write(text)
                    await file.truncate()
            finally:
                seek.cancel()

    formatErrs = tuple(
        err
        for err in await gather(
            *map(replaceInJournal, journals), return_exceptions=True
        )
        if err
    )
    if formatErrs:
        raise BaseExceptionGroup("", formatErrs)

    exit(0)


def parser(parent: Callable[..., ArgumentParser] | None = None):
    prog = argv[0]

    parser = (ArgumentParser if parent is None else parent)(
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

    @wraps(main)
    async def invoke(ns: Namespace):
        await main(Arguments(find=ns.find, replace=ns.replace))

    parser.set_defaults(invoke=invoke)
    return parser


if __name__ == "__main__":
    basicConfig(level=INFO)
    entry = parser().parse_args(argv[1:])
    run(entry.invoke(entry))
