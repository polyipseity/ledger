from argparse import ArgumentParser, Namespace
from asyncio import run
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from logging import INFO, basicConfig, info
from sys import argv, exit
from typing import final

from anyio import Path

from .util import (
    file_update_if_changed,
    find_all_journals,
    gather_and_raise,
    get_script_folder,
)

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
    folder = get_script_folder()

    journals = await find_all_journals(folder)
    info(f'journals: {", ".join(map(str, journals))}')

    async def replace_in_journal(journal: Path):
        def updater(read: str) -> str:
            return read.replace(args.find, args.replace)

        await file_update_if_changed(journal, updater)

    await gather_and_raise(*map(replace_in_journal, journals))

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
