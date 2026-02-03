from argparse import ArgumentParser, Namespace
from asyncio import BoundedSemaphore, create_subprocess_exec, create_task, gather, run
from asyncio.subprocess import DEVNULL, PIPE
from dataclasses import dataclass
from functools import wraps
from glob import iglob
from inspect import currentframe, getframeinfo
from logging import INFO, basicConfig, info
from os import cpu_count
from shutil import which
from sys import argv, exit
from typing import Callable, Iterable, cast, final

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
    check: bool
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

    unformatted_files = list[Path]()

    async def formatJournal(journal: Path):
        async with _SUBPROCESS_SEMAPHORE:
            proc = await create_subprocess_exec(
                hledger_prog,
                "--file",
                journal,
                "--strict",
                "print",
                stdin=DEVNULL,
                stdout=PIPE,
                stderr=PIPE,
            )
            stdout, stderr = (
                std.decode().replace("\r\n", "\n") for std in await proc.communicate()
            )
            if await proc.wait():
                raise ChildProcessError(proc.returncode, stderr)

        async with await journal.open(
            mode="r+t", encoding="UTF-8", errors="strict", newline=None
        ) as file:
            read = await file.read()
            seek = create_task(file.seek(0))
            try:
                header = "\n".join(
                    line for line in read.splitlines() if line.startswith("include ")
                )
                text = f"""{header}

{stdout.strip()}

"""

                def sortProps(line: str):
                    components = line.split("  ;", 1)
                    if len(components) != 2:
                        return line
                    code, cmt = components

                    def group(sections: Iterable[str]):
                        ret = list[tuple[str, str]]()
                        for section in sections:
                            section = cast(
                                tuple[str] | tuple[str, str],
                                tuple(section.split(":", 1)),
                            )
                            if len(section) == 2:
                                ret.append(section)
                                continue
                            if ret:
                                yield ret
                                ret = []
                            yield section[0]
                        if ret:
                            yield ret

                    return f"""{code}  {f'''; {", ".join(
                        group.strip()
                        if isinstance(group, str)
                        else ", ".join(
                            ": ".join(prop)
                            for prop in sorted(
                                tuple(cmp.strip() for cmp in group) for group in group
                            )
                        )
                        for group in group(cmt.split(","))
                    )}'''.strip()}"""

                formatted_text = "\n".join(map(sortProps, text.splitlines()))
                # Normalize line endings for comparison
                normalized_read = read.replace("\r\n", "\n")

                if formatted_text != normalized_read:
                    if args.check:
                        unformatted_files.append(journal)
                    else:
                        await seek
                        await file.write(formatted_text)
                        await file.truncate()
            finally:
                seek.cancel()

    errors = tuple(
        err
        for err in await gather(*map(formatJournal, journals), return_exceptions=True)
        if err
    )
    if errors:
        raise BaseExceptionGroup("", errors)

    if args.check and unformatted_files:
        print("The following files are not properly formatted:")
        for file in unformatted_files:
            print(f"  {file}")
        exit(1)

    exit(0)


def parser(parent: Callable[..., ArgumentParser] | None = None):
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
