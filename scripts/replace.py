"""Replace text across all journal files in the repository.

This script scans every `*.journal` file and replaces occurrences of the
provided search text with the replacement text. Changes are written only
when the file contents change.
"""

from argparse import ArgumentParser, Namespace
from asyncio import run
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from logging import INFO, basicConfig, info
from os import PathLike
from sys import argv, exit
from typing import final

from .util.concurrency import gather_and_raise
from .util.files import file_update_if_changed, get_ledger_folder
from .util.journals import find_all_journals

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
    """CLI arguments for `scripts.replace`.

    Attributes:
        find: The literal text to search for.
        replace: The replacement text to write where matches are found.
    """

    find: str
    replace: str


async def main(args: Arguments) -> None:
    """Run a global find-and-replace across all journal files.

    Loads each journal, applies a simple string replacement and writes the
    file back only when the content changed.
    """

    folder = get_ledger_folder()

    journals = await find_all_journals(folder)
    info(f'journals: {", ".join(map(str, journals))}')

    async def replace_in_journal(journal: PathLike[str]) -> None:
        def updater(read: str) -> str:
            return read.replace(args.find, args.replace)

        await file_update_if_changed(journal, updater)

    await gather_and_raise(*map(replace_in_journal, journals))

    exit(0)


def parser(parent: Callable[..., ArgumentParser] | None = None) -> ArgumentParser:
    """Create and return the CLI ArgumentParser for the replace script.

    The returned parser sets an `invoke` coroutine default that executes
    :func:`main` when run.
    """

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
    async def invoke(ns: Namespace) -> None:
        await main(Arguments(find=ns.find, replace=ns.replace))

    parser.set_defaults(invoke=invoke)
    return parser


if __name__ == "__main__":
    basicConfig(level=INFO)
    entry = parser().parse_args(argv[1:])
    run(entry.invoke(entry))
