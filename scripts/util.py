"""Utility helpers used by repository scripts.

This module provides small, well-documented utilities used across the
`scripts/` package. Public helpers cover:

- locating the calling script's folder (`get_script_folder`)
- discovering journal files under the repository (`find_monthly_journals`,
  `find_all_journals`)
- filtering monthly journals by inclusive month windows
  (`filter_journals_between`)
- running `hledger` subprocesses (`run_hledger`)
- safely updating journal files only when contents change
  (`file_update_if_changed`)
- parsing loose ISO-like period strings for start/end semantics
  (`parse_period_start`, `parse_period_end`)
- parsing human-formatted amounts (`parse_amount`)
- small concurrency helpers used by scripts (`gather_and_raise`)

Constants:

- `DEFAULT_AMOUNT_DECIMAL_PLACES` - default number of decimal places to use
  when formatting amounts in scripts.
"""

import asyncio
from asyncio import BoundedSemaphore, create_subprocess_exec
from asyncio.subprocess import DEVNULL, PIPE
from calendar import monthrange
from collections.abc import Awaitable, Callable, Iterable, Sequence
from contextlib import suppress
from datetime import datetime
from glob import iglob
from inspect import currentframe, getframeinfo
from os import cpu_count
from shutil import which
from subprocess import CalledProcessError

from anyio import Path

__all__ = (
    "DEFAULT_AMOUNT_DECIMAL_PLACES",
    "get_script_folder",
    "find_monthly_journals",
    "find_all_journals",
    "filter_journals_between",
    "file_update_if_changed",
    "run_hledger",
    "parse_period_start",
    "parse_period_end",
    "parse_amount",
    "gather_and_raise",
)

DEFAULT_AMOUNT_DECIMAL_PLACES = 2
"""Default number of decimal places used when scripts format monetary amounts.

Scripts that format monetary values should use this constant when constructing
format strings (for example: `f"{value:.{DEFAULT_AMOUNT_DECIMAL_PLACES}f}"`).
"""
_SUBPROCESS_SEMAPHORE = BoundedSemaphore(cpu_count() or 4)


def get_script_folder() -> Path:
    """Return the Path of the folder containing the caller script.

    This inspects the current Python stack and returns the directory containing
    the calling module's source file. When used by modules under the
    `scripts` package (e.g. `scripts.format`), this resolves to the
    repository's `scripts/` folder which is the intended caller behaviour.
    """
    frame = currentframe()
    if frame is None:
        raise ValueError(frame)
    return Path(getframeinfo(frame).filename).parent


async def run_hledger(
    journal: Path, *args: str, raise_on_error: bool = True
) -> tuple[str, str, int]:
    """Run `hledger --file <journal> --strict <*args>` and return (stdout, stderr, returncode).

    If ``raise_on_error`` is True (the default), a non-zero exit status will
    raise :class:`subprocess.CalledProcessError` which includes the returncode
    and `stderr` text.

    Raises
    ------
    FileNotFoundError
        If the `hledger` executable cannot be found.
    subprocess.CalledProcessError
        If ``raise_on_error`` is True and the process exits with a non-zero status.
    """
    hledger_prog = which("hledger")
    if hledger_prog is None:
        raise FileNotFoundError("hledger executable not found in PATH")

    async with _SUBPROCESS_SEMAPHORE:
        cli = (hledger_prog, "--file", str(journal), "--strict", *args)
        proc = await create_subprocess_exec(
            *cli,
            stdin=DEVNULL,
            stdout=PIPE,
            stderr=PIPE,
        )
        out_bytes, err_bytes = await proc.communicate()
        stdout = out_bytes.decode().replace("\r\n", "\n")
        stderr = err_bytes.decode().replace("\r\n", "\n")
        returncode = await proc.wait()
        if raise_on_error and returncode:
            raise CalledProcessError(
                returncode,
                cli,
                output=stdout,
                stderr=stderr,
            )
        return stdout, stderr, returncode


async def gather_and_raise(*awaitables: Awaitable[object]) -> None:
    """Run many awaitables concurrently and raise grouped exceptions.

    This helper wraps :func:`asyncio.gather(..., return_exceptions=True)` and
    converts any returned exceptions into a single :class:`BaseExceptionGroup`.

    Parameters
    ----------
    *awaitables: Awaitable[object]
        The awaitables (coroutines/futures) to run concurrently.

    Raises
    ------
    BaseExceptionGroup
        If any of the awaitables raised; the group's members will be the
        individual exceptions raised by those awaitables.
    """
    results = await asyncio.gather(*awaitables, return_exceptions=True)
    errs = tuple(err for err in results if isinstance(err, BaseException))
    if errs:
        raise BaseExceptionGroup("One or more tasks failed", errs)


async def find_monthly_journals(
    folder: Path, files: Iterable[str] | None = None
) -> Sequence[Path]:
    """Return resolved Paths for monthly journal files under the repository.

    The function looks for files matching the pattern ``YYYY-MM/*.journal`` under
    ``folder.parent``. If ``files`` is supplied, those are resolved (strict)
    and returned instead. The function returns the resolved paths in the same
    order the filesystem yields them.

    Parameters
    ----------
    folder: Path
        Path somewhere inside the repository (typically the script folder).
    files: Iterable[str] | None
        Optional explicit file paths to resolve and return.

    Returns
    -------
    Sequence[Path]
        A sequence of resolved :class:`anyio.Path` objects.
    """
    if files:
        return await asyncio.gather(
            *(Path(path).resolve(strict=True) for path in files)
        )

    pattern = "**/*[0123456789][0123456789][0123456789][0123456789]-[0123456789][0123456789]/*.journal"
    return await asyncio.gather(
        *(
            Path(folder.parent, path).resolve(strict=True)
            for path in iglob(pattern, root_dir=folder.parent, recursive=True)
        )
    )


async def find_all_journals(folder: Path) -> Sequence[Path]:
    """Return resolved Paths for all journal files under the repository.

    The function finds all ``*.journal`` files under ``folder.parent`` and
    returns the resolved :class:`anyio.Path` objects.

    Parameters
    ----------
    folder: Path
        Path somewhere inside the repository (typically the script folder).

    Returns
    -------
    Sequence[Path]
        A sequence of resolved :class:`anyio.Path` objects.
    """
    return await asyncio.gather(
        *(
            Path(folder.parent, path).resolve(strict=True)
            for path in iglob("**/*.journal", root_dir=folder.parent, recursive=True)
        )
    )


def make_datetime_range_filters(
    from_datetime: datetime | None, to_datetime: datetime | None
) -> tuple[Callable[[datetime], bool], Callable[[datetime], bool]]:
    """Create `from` and `to` predicates from optional datetimes.

    The returned pair of callables mirrors the common pattern used by scripts:
    - ``from_filter(dt)`` returns ``True`` if the provided ``dt`` is on/after
      the supplied ``from_datetime`` (or always True when ``from_datetime`` is
      ``None``).
    - ``to_filter(dt)`` returns ``True`` if the provided ``dt`` is on/before
      the supplied ``to_datetime`` (or always True when ``to_datetime`` is
      ``None``).

    Parameters
    ----------
    from_datetime: datetime | None
        Inclusive lower bound of the window.
    to_datetime: datetime | None
        Inclusive upper bound of the window.

    Returns
    -------
    tuple[Callable[[datetime], bool], Callable[[datetime], bool]]
        The (from_filter, to_filter) pair.
    """
    if from_datetime is None:

        def from_filter(dt: datetime) -> bool:
            return True

    else:

        def from_filter(dt: datetime) -> bool:
            return from_datetime <= dt

    if to_datetime is None:

        def to_filter(dt: datetime) -> bool:
            return True

    else:

        def to_filter(dt: datetime) -> bool:
            return dt <= to_datetime

    return from_filter, to_filter


def filter_journals_between(
    journals: Iterable[Path],
    from_datetime: datetime | None,
    to_datetime: datetime | None,
) -> Sequence[Path]:
    """Filter monthly journals by inclusive month-range matching behaviour used by scripts.

    Each journal's month is determined by `journal.parent.name` as YYYY-MM and the
    journal is included if the month (treated as the month's full span)
    intersects the provided [from_datetime, to_datetime] window.

    The function uses :func:`make_datetime_range_filters` to construct the
    from/to predicates to avoid duplicating that common logic across
    scripts.
    """
    from_filter, to_filter = make_datetime_range_filters(from_datetime, to_datetime)

    def month_end(dt: datetime) -> datetime:
        return dt.replace(
            day=monthrange(dt.year, dt.month)[1],
            hour=23,
            minute=59,
            second=59,
            microsecond=999999,
            fold=1,
        )

    ret: list[Path] = []
    for journal in journals:
        try:
            to_date = datetime.fromisoformat(f"{journal.parent.name}-01")
        except Exception:
            continue
        if to_filter(month_end(to_date)) and from_filter(to_date):
            ret.append(journal)
    return ret


async def file_update_if_changed(journal: Path, updater: Callable[[str], str]) -> bool:
    """Open `journal`, read content, run `updater(read)` and write/truncate only if changed.

    Returns True if file was changed.
    """
    async with await journal.open(
        mode="r+t", encoding="UTF-8", errors="strict", newline=None
    ) as file:
        read = await file.read()
        # Seek back to the start before writing. Using an explicit await is
        # clearer and avoids creating background tasks that need cancelling.
        await file.seek(0)

        text = updater(read)
        if text != read:
            await file.write(text)
            await file.truncate()
            return True
        return False


def parse_period_start(date_string: str) -> datetime:
    """Parse a loose ISO-style date into a period-start datetime.

    Accepts strings like ``YYYY``, ``YYYY-MM``, and ``YYYY-MM-DD`` and returns
    an appropriate :class:`datetime` that represents the start of the supplied
    period (for example: ``"2024"`` ⇒ ``2024-01-01``).

    Parameters
    ----------
    date_string: str
        The date-like string in ISO-like format.

    Returns
    -------
    datetime
        An ISO-converted :class:`datetime` at the period start.

    Raises
    ------
    ValueError
        If the string cannot be parsed as one of the accepted forms.
    """
    try:
        return datetime.fromisoformat(date_string)
    except ValueError:
        with suppress(ValueError):
            return datetime.fromisoformat(f"{date_string}-01")
        with suppress(ValueError):
            return datetime.fromisoformat(f"{date_string}-01-01")
        raise


def parse_period_end(date_string: str) -> datetime:
    """Parse a loose ISO-style date into a period-end datetime.

    The returned :class:`datetime` represents the end of the supplied period and
    accepts the same loose ISO-like forms as :func:`parse_period_start` (for
    example ``"2024-02"`` ⇒ ``2024-02-29`` in leap years).

    Parameters
    ----------
    date_string: str
        The date-like string in ISO-like format.

    Returns
    -------
    datetime
        An ISO-converted :class:`datetime` at the period end.

    Raises
    ------
    ValueError
        If the string cannot be parsed as one of the accepted forms.
    """
    try:
        return datetime.fromisoformat(date_string)
    except ValueError:
        for day in range(31, 27, -1):
            with suppress(ValueError):
                return datetime.fromisoformat(f"{date_string}-{day}")
        for day in range(31, 27, -1):
            with suppress(ValueError):
                return datetime.fromisoformat(f"{date_string}-12-{day}")
        raise


def parse_amount(float_str: str) -> float:
    """Parse a human-formatted amount string into a float.

    Accepts amounts using spaces or commas as grouping separators and supports
    either '.' or ',' as the decimal separator. Examples:
    - "1,234.56" => 1234.56 (comma as thousands separator)
    - "1 234,56" => 1234.56 (space as thousands separator, comma as decimal)

    The heuristic used:
    - If both "." and "," are present treat "," as thousands separator.
    - If only "," is present treat "," as decimal separator.
    - Spaces are always ignored.
    """
    s = float_str.strip()
    s = s.replace(" ", "")
    if "." in s and "," in s:
        # comma used as thousands separator
        s = s.replace(",", "")
    elif "," in s:
        # comma used as decimal separator
        s = s.replace(",", ".")
    return float(s)
