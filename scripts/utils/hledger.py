"""Running the hledger binary, and the text helpers its callers share.

Every script that shells out to hledger comes through :func:`run_hledger`, so
the invocation contract — the managed binary, ``--strict``, the decoded streams
— changes in one place. The journal model that ``hledger print -O json`` yields
lives in :mod:`scripts.clopen`, its only consumer. The dependency runs one way:
:mod:`scripts.utils.journals` imports this module and never the reverse.
"""

import logging
import sys
from os import PathLike, cpu_count, fspath
from pathlib import Path
from re import Pattern, compile
from shutil import which
from subprocess import DEVNULL, PIPE
from typing import final

from anyio import Semaphore, run_process

"""Public symbols exported by this module."""
__all__ = (
    "HledgerRunError",
    "MONTH_PATTERN",
    "first_line",
    "run_hledger",
)

"""Module-level logger for hledger subprocess failures."""
logger = logging.getLogger(__name__)

"""Pattern a ``YYYY-MM`` month name must fully match."""
MONTH_PATTERN: Pattern[str] = compile("[0-9]{4}-[0-9]{2}")

"""Limits concurrent hledger subprocess invocations to avoid resource exhaustion."""
_SUBPROCESS_SEMAPHORE = Semaphore(cpu_count() or 4)


def _managed_hledger_path() -> Path:
    """Return the filesystem path where the bun-managed hledger binary is installed.

    The binary is placed at ``<repo_root>/node_modules/.bin/hledger[.exe]`` by
    ``bun run hledger:install`` (``scripts/install-hledger.mjs``). This file
    lives at ``scripts/utils/hledger.py``, so the repo root is three ``parent``
    steps up.
    """
    binary_name = "hledger.exe" if sys.platform == "win32" else "hledger"
    return Path(__file__).parent.parent.parent / "node_modules" / ".bin" / binary_name


def _find_hledger() -> str:
    """Locate the hledger executable, preferring the bun-managed project-local binary.

    Search order:
    1. ``<repo_root>/node_modules/.bin/hledger[.exe]`` — installed by
       ``bun run hledger:install``.
    2. Whatever ``shutil.which("hledger")`` finds on the system ``PATH``.

    Returns
    -------
    str
        Absolute path to the hledger executable as a ``str``.

    Raises
    ------
    FileNotFoundError
        If hledger is found neither in ``node_modules/.bin/`` nor on ``PATH``.
    """
    managed = _managed_hledger_path()
    if managed.exists():
        return fspath(managed)
    found = which("hledger")
    if found is None:
        raise FileNotFoundError(
            "hledger executable not found in node_modules/.bin/ or PATH; "
            "run `bun run hledger:install` to install the managed binary"
        )
    return found


@final
class HledgerRunError(RuntimeError):
    """A hledger invocation that exited with a non-zero return code.

    Attributes:
        command: The command line as it was run, hledger's path first.
        stdout: Standard output, decoded and with CRLF line endings normalised.
        stderr: Standard error, decoded and with CRLF line endings normalised.
        returncode: The exit code the process reported.
    """

    command: tuple[str, ...]
    stdout: str
    stderr: str
    returncode: int

    def __init__(
        self, command: tuple[str, ...], stdout: str, stderr: str, returncode: int
    ) -> None:
        """Build the message from the command, its exit code, and its error text."""
        message = f"hledger {command!r} exited with returncode={returncode}"
        detail = stderr.strip() or stdout.strip()
        super().__init__(f"{message}: {detail}" if detail else message)
        self.command = command
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


async def run_hledger(
    journal: PathLike[str] | str,
    *args: str,
    raise_on_error: bool = True,
    strict: bool = True,
    log_on_error: bool = True,
) -> tuple[str, str, int]:
    """Run ``hledger --file <journal> [--strict] <args>`` and return its result.

    The subprocess is never asked to raise, so a non-zero exit reaches the
    manual handling below in every case and ``raise_on_error=False`` really
    reports the failure instead of failing the call.

    Args:
        journal: The journal to pass to ``--file``, as a path or a path string.
        *args: Further hledger arguments, such as ``"check"``.
        raise_on_error: Raise :class:`HledgerRunError` on a non-zero exit
            instead of returning it.
        strict: Pass ``--strict``, so an undeclared account or commodity fails.
        log_on_error: Log both streams at ERROR level on a non-zero exit.

    Returns:
        The decoded standard output and standard error, with CRLF line endings
        normalised, and the exit code.

    Raises:
        FileNotFoundError: When hledger is available neither in
            ``node_modules/.bin/`` nor on ``PATH``.
        HledgerRunError: When the process exits non-zero and ``raise_on_error``
            is set.
    """
    cli = (
        _find_hledger(),
        "--file",
        fspath(journal),
        *(("--strict",) if strict else ()),
        *args,
    )
    async with _SUBPROCESS_SEMAPHORE:
        proc = await run_process(
            cli,
            check=False,
            stdin=DEVNULL,
            stdout=PIPE,
            stderr=PIPE,
        )
        stdout = proc.stdout.decode().replace("\r\n", "\n")
        stderr = proc.stderr.decode().replace("\r\n", "\n")
        returncode = proc.returncode
        if returncode and log_on_error:
            logger.error(
                "hledger %r exited with returncode=%d\nstdout:\n%s\nstderr:\n%s",
                cli,
                returncode,
                stdout,
                stderr,
            )
        if raise_on_error and returncode:
            raise HledgerRunError(cli, stdout, stderr, returncode)
        return stdout, stderr, returncode


def first_line(text: str) -> str:
    """Return the first non-empty line of ``text``, or a placeholder when empty."""
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return "(no output)"
