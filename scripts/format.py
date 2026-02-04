"""Format journal files using `hledger print` output.

This module uses `hledger print` to obtain a canonical representation of a
journal, post-processes comment properties for consistent ordering, and
writes the formatted output back to the journal (or reports files that
would change when run with `--check`).
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
    file_update_if_changed,
    find_monthly_journals,
    gather_and_raise,
    get_script_folder,
    run_hledger,
)

__all__ = ("Arguments", "main", "parser")


def _sort_props(line: str) -> str:
    """Format a single line comments by grouping and sorting key:value properties.

    The function accepts lines of the form ``<code>  ; <comment>`` and will
    group consecutive ``key:value`` segments, sort properties within each
    group by key, and reassemble the comment in a consistent, human-friendly
    order. Lines without the ``  ;`` separator are returned unchanged.
    """
    components = line.split("  ;", 1)
    if len(components) != 2:
        return line
    code, cmt = components

    formatted_parts: list[str] = []
    for part in _group_props(cmt.split(",")):
        if isinstance(part, str):
            formatted_parts.append(part.strip())
            continue
        # part is a list[tuple[str,str]] - sort by key then join
        formatted_parts.append(
            ", ".join(
                ": ".join(prop)
                for prop in sorted(tuple(cmp.strip() for cmp in grp) for grp in part)
            )
        )

    return f"{code}  ; {', '.join(formatted_parts)}"


def _group_props(sections: Iterable[str]):
    """Yield grouped property parts used by the formatter.

    The helper mirrors the previous inner helper in `sortProps`, grouping
    consecutive `key:value` pairs and yielding either the key (str) or a
    list of `(key, value)` tuples when appropriate. Extracted to make unit
    testing straightforward.
    """
    ret: list[tuple[str, str]] = []
    for section in sections:
        sec = tuple(section.split(":", 1))
        if len(sec) == 2:
            ret.append(sec)
            continue
        if ret:
            yield ret
            ret = []
        yield sec[0]
    if ret:
        yield ret


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
    """CLI arguments for `scripts.format`.

    Attributes:
        check: When True, detect unformatted files without modifying them.
        files: Optional list of journal file paths to format; when omitted all
               monthly journals are processed.
    """

    check: bool
    files: Iterable[str] | None = None


async def _format_journal(journal: Path, unformatted_files: list[Path], check: bool):
    """Format a single journal using the output of `hledger print`.

    The function constructs a normalized header, replaces the journal body
    with the `hledger print` result (post-processed with property sorting)
    and writes back the file. When `check` is True, files that would be
    modified are appended to `unformatted_files` instead of failing.
    """

    stdout, stderr, returncode = await run_hledger(journal, "print")
    # `run_hledger` raises a CalledProcessError on non-zero exit by default,
    # so no explicit returncode check is necessary here.

    def updater(read: str) -> str:
        header = "\n".join(
            line for line in read.splitlines() if line.startswith("include ")
        )
        text = f"""{header}

{stdout.strip()}

"""

        formatted_text = "\n".join(map(_sort_props, text.splitlines()))
        return formatted_text

    changed = await file_update_if_changed(journal, updater)
    if changed and check:
        unformatted_files.append(journal)


async def main(args: Arguments):
    """Format monthly journal files according to repository conventions.

    Iterates selected monthly journals, runs formatting and optionally
    reports files that are not formatted when `args.check` is True.
    """

    folder = get_script_folder()

    journals = await find_monthly_journals(folder, args.files)
    info(f'journals: {", ".join(map(str, journals))}')

    unformatted_files = list[Path]()

    await gather_and_raise(
        *(_format_journal(j, unformatted_files, args.check) for j in journals)
    )

    if args.check and unformatted_files:
        print("The following files are not properly formatted:")
        for file in unformatted_files:
            print(f"  {file}")
        exit(1)

    exit(0)


def parser(parent: Callable[..., ArgumentParser] | None = None):
    """Create and return the CLI ArgumentParser for the format script.

    The parser supports a `--check` flag and an optional list of files to
    operate on. The returned parser sets an `invoke` coroutine default which
    calls :func:`main`.
    """

    prog = argv[0]

    parser = (ArgumentParser if parent is None else parent)(
        prog=prog,
        description="format journals",
        add_help=True,
        allow_abbrev=False,
        exit_on_error=False,
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help="check if files are formatted without modifying them",
    )

    parser.add_argument(
        "files",
        nargs="*",
        help="Optional list of journal files to format/check",
    )

    @wraps(main)
    async def invoke(ns: Namespace):
        await main(Arguments(check=ns.check, files=getattr(ns, "files", None)))

    parser.set_defaults(invoke=invoke)
    return parser


if __name__ == "__main__":
    basicConfig(level=INFO)
    entry = parser().parse_args(argv[1:])
    run(entry.invoke(entry))
