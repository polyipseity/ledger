"""Run `hledger check` against monthly journal files.

This script runs a comprehensive set of `hledger check` subcommands
against each selected monthly journal and reports failures by raising
exceptions from the subprocess call.
"""

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
    JournalRunContext,
    find_monthly_journals,
    gather_and_raise,
    get_script_folder,
    run_hledger,
)

__all__ = ("Arguments", "main", "parser")

_HLEDGER_CHECKS = (
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
    """CLI arguments for `scripts.check`.

    Attributes:
        files: Optional list of journal files to check; when omitted all monthly
               journals are checked.
    """

    files: Iterable[str] | None = None


async def main(args: Arguments):
    """Run `hledger check` on the set of selected monthly journals.

    For each selected journal this runs `hledger check` with a set of
    helpful checks (accounts, assertions, balanced, parseable, etc.).
    """

    folder = get_script_folder()

    journals = await find_monthly_journals(folder, args.files)
    info(f'journals: {", ".join(map(str, journals))}')

    async with JournalRunContext(Path(__file__), journals) as run:
        if run.skipped:
            info(f"skipped: {', '.join(map(str, run.skipped))}")

        async def check_journal(journal: Path):
            await run_hledger(journal, "check", *_HLEDGER_CHECKS)
            # If the check returned successfully record it for this session
            run.report_success(journal)

        await gather_and_raise(*map(check_journal, run.to_process))

    exit(0)


def parser(parent: Callable[..., ArgumentParser] | None = None):
    """Create and return the CLI ArgumentParser for the check script.

    The parser accepts an optional list of files to check and sets an
    `invoke` coroutine default to run :func:`main`.
    """

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
