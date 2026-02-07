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
from os import PathLike
from sys import argv, exit
from typing import final

from anyio import Path

from .utils.cache import JournalRunContext
from .utils.concurrency import gather_and_raise
from .utils.files import get_ledger_folder
from .utils.journals import find_monthly_journals, format_journal_list, run_hledger

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


async def main(args: Arguments) -> None:
    """Run `hledger check` on the set of selected monthly journals.

    For each selected journal this runs `hledger check` with a set of
    helpful checks (accounts, assertions, balanced, parseable, etc.).
    """

    folder = get_ledger_folder()

    journals = await find_monthly_journals(folder, args.files)
    info("journals:\n%s", format_journal_list(journals, max_items=8))

    async with JournalRunContext(Path(__file__), journals) as run:
        if run.skipped:
            info("skipped:\n%s", format_journal_list(run.skipped, max_items=8))

        async def check_journal(journal: PathLike[str]) -> None:
            """Run the set of hledger checks for a single journal and record success.

            This coroutine runs :func:`run_hledger` with the configured set of
            check arguments for the supplied ``journal`` and records the journal
            as processed on success.
            """
            await run_hledger(journal, "check", *_HLEDGER_CHECKS)
            # If the check returned successfully record it for this session
            run.report_success(journal)

        await gather_and_raise(*map(check_journal, run.to_process))

        # Summarise processed journals for quick inspection
        if run.reported:
            info("processed:\n%s", format_journal_list(run.reported, max_items=8))

    exit(0)


def parser(parent: Callable[..., ArgumentParser] | None = None) -> ArgumentParser:
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
    async def invoke(ns: Namespace) -> None:
        """Invoke the main coroutine using parsed Namespace values.

        The function adapts the parsed :class:`argparse.Namespace` into the
        :class:`Arguments` dataclass expected by :func:`main`.
        """
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
