"""hledger invocation and the journal model the scripts share.

Every script that shells out to hledger, and every script that reads
``hledger print -O json``, comes through here, so the invocation contract and
the shape of hledger's output change in one file. The dependency between this
module and :mod:`scripts.utils.journals` runs one way only: that module imports
this one, so nothing here may import it back.
"""

import logging
import sys
from calendar import monthrange
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from os import PathLike, cpu_count, fspath
from pathlib import Path
from re import Pattern, compile
from shutil import which
from subprocess import DEVNULL, PIPE
from typing import final

from anyio import Semaphore, run_process
from pydantic import BaseModel, ConfigDict, RootModel, ValidationError

from .files import get_script_folder

"""Public symbols exported by this module."""
__all__ = (
    "CLOSING_DESCRIPTION",
    "MONTH_PATTERN",
    "OPENING_DESCRIPTION",
    "Amount",
    "BalanceAssertion",
    "DefectKind",
    "HledgerRunError",
    "Journal",
    "JournalDocument",
    "Posting",
    "Quantity",
    "Transaction",
    "Unreadable",
    "display_path",
    "first_line",
    "hledger_output",
    "last_day",
    "load_journal",
    "money",
    "run_hledger",
)

"""Module-level logger for hledger subprocess failures."""
logger = logging.getLogger(__name__)

"""Pattern a ``YYYY-MM`` month name must fully match."""
MONTH_PATTERN: Pattern[str] = compile("[0-9]{4}-[0-9]{2}")

"""Description of the transaction that carries a month's opening balances."""
OPENING_DESCRIPTION = "opening balances"

"""Description of the transaction that carries a month's closing balances."""
CLOSING_DESCRIPTION = "closing balances"

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


class Quantity(BaseModel):
    """Exact decimal quantity as hledger reports it."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    decimalMantissa: int
    decimalPlaces: int

    @property
    def value(self) -> Decimal:
        """Return the quantity as an exact decimal."""
        return Decimal(self.decimalMantissa).scaleb(-self.decimalPlaces)

    @property
    def zero(self) -> Decimal:
        """Return zero at the same scale as the quantity, for reporting."""
        return Decimal(0).scaleb(-self.decimalPlaces)


class Amount(BaseModel):
    """One commodity amount inside a posting or a balance assertion."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    acommodity: str
    aquantity: Quantity


class BalanceAssertion(BaseModel):
    """Balance assertion attached to a closing posting."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    baamount: Amount


class Posting(BaseModel):
    """One posting of a transaction."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    paccount: str
    pamount: list[Amount]
    pbalanceassertion: BalanceAssertion | None = None


class Transaction(BaseModel):
    """One transaction as ``hledger print -O json`` reports it.

    ``tindex`` is hledger's journal-order index, the only reliable ordering
    signal: the time of day lives in the ``time`` tag, not in ``tdate``.
    """

    model_config = ConfigDict(extra="ignore", frozen=True)

    tdate: str
    tdescription: str
    tindex: int
    tpostings: list[Posting]
    ttags: list[tuple[str, str]]


class JournalDocument(RootModel[list[Transaction]]):
    """Top-level JSON document of one journal, holding its transactions."""


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
class Journal:
    """A monthly journal reduced to the transactions the scripts inspect.

    Attributes:
        path: The journal file on disk.
        month: The ``YYYY-MM`` month taken from the journal's directory name.
        transactions: Every transaction, in journal order.
        opening: The opening balance transaction, when the month has one.
        closing: The closing balance transaction, when the month has one.
    """

    path: Path
    month: str
    transactions: Sequence[Transaction]
    opening: Transaction | None
    closing: Transaction | None


@final
class Unreadable(Exception):
    """A journal whose contents could not be read.

    Attributes:
        detail: The reason, ready to become an :attr:`DefectKind.UNREADABLE`
            defect detail.
    """

    detail: str

    def __init__(self, detail: str) -> None:
        """Store ``detail`` as the reason the journal could not be read."""
        super().__init__(detail)
        self.detail = detail


async def hledger_output(journal: PathLike[str], *args: str) -> tuple[str, str, int]:
    """Run hledger on ``journal`` and return its output, error text, and exit code.

    The run never raises and is never strict: a broken journal must become a
    reported defect rather than a crash, and account declarations play no part
    in what a caller of this helper reads.
    """
    return await run_hledger(
        journal,
        *args,
        strict=False,
        raise_on_error=False,
        log_on_error=False,
    )


async def load_journal(path: Path) -> Journal:
    """Return ``path`` parsed into the boundary data the scripts inspect.

    hledger runs without ``--strict`` because account declarations play no part
    in balance arithmetic, so that a journal missing declarations still counts.

    Args:
        path: The monthly journal to read, whose parent directory names the
            month.

    Returns:
        The journal's transactions with its opening and closing balance
        transactions picked out.

    Raises:
        Unreadable: When the month directory is not named after a calendar
            month, or when hledger fails, prints nothing, or prints something
            that is not a hledger journal document.
    """
    month = path.parent.name
    if MONTH_PATTERN.fullmatch(month) is None:
        raise Unreadable(f"month directory {month!r} is not named YYYY-MM")
    try:
        last_day(month)
    except ValueError as exc:
        raise Unreadable(f"month directory {month!r} is not a calendar month") from exc
    stdout, stderr, code = await hledger_output(path, "print", "-O", "json")
    if code != 0:
        raise Unreadable(f"hledger print exited {code}: {first_line(stderr)}")
    if not stdout.strip():
        raise Unreadable("hledger print produced no output")
    try:
        document = JournalDocument.model_validate_json(stdout)
    except ValidationError as exc:
        raise Unreadable(
            f"hledger print produced an unexpected document: {first_line(str(exc))}"
        ) from exc
    transactions = document.root
    return Journal(
        path=path,
        month=month,
        transactions=transactions,
        opening=_boundary(transactions, OPENING_DESCRIPTION, last=False),
        closing=_boundary(transactions, CLOSING_DESCRIPTION, last=True),
    )


def _boundary(
    transactions: Sequence[Transaction], description: str, *, last: bool
) -> Transaction | None:
    """Return the boundary transaction described by ``description``, if any."""
    matches = [
        transaction
        for transaction in transactions
        if transaction.tdescription == description
    ]
    if not matches:
        return None
    return matches[-1] if last else matches[0]


def last_day(month: str) -> str:
    """Return the last date of ``month`` as a ``YYYY-MM-DD`` string.

    Raises:
        ValueError: When ``month`` is not a calendar month.
    """
    year, _, number = month.partition("-")
    return f"{month}-{monthrange(int(year), int(number))[1]:02d}"


def money(amount: Amount) -> str:
    """Return ``amount`` as an exact quantity followed by its commodity."""
    return f"{amount.aquantity.value} {amount.acommodity}"


def first_line(text: str) -> str:
    """Return the first non-empty line of ``text``, or a placeholder when empty."""
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return "(no output)"


def display_path(path: Path) -> str:
    """Return ``path`` relative to the repository root when it lies inside it."""
    try:
        return fspath(path.relative_to(fspath(get_script_folder(depth=2))))
    except ValueError:
        return fspath(path)


class DefectKind(StrEnum):
    """Kind of monthly boundary defect a verifier reports."""

    MISSING_OPENING = "missing_opening"
    MISSING_CLOSING = "missing_closing"
    UNEXPECTED_BOUNDARY = "unexpected_boundary"
    CLOSING_NOT_ZERO = "closing_not_zero"
    CLOSING_INCOMPLETE = "closing_incomplete"
    OPENING_MISMATCH = "opening_mismatch"
    BOUNDARY_UNORDERED = "boundary_unordered"
    UNREADABLE = "unreadable"
