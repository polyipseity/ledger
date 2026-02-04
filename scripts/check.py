from argparse import ArgumentParser, Namespace
from asyncio import run
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from functools import wraps
from logging import INFO, basicConfig, info
from sys import argv, exit
from typing import final

from anyio import Path

from .util import (
    find_monthly_journals,
    gather_and_raise,
    get_script_folder,
    run_hledger,
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
    files: Iterable[str] | None = None


async def main(args: Arguments):
    folder = get_script_folder()

    journals = await find_monthly_journals(folder, args.files)
    info(f'journals: {", ".join(map(str, journals))}')

    async def check_journal(journal: Path):
        await run_hledger(
            journal,
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
        )

    await gather_and_raise(*map(check_journal, journals))

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
