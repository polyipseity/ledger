"""Journal discovery, date parsing and hledger subprocess helpers."""

from asyncio import BoundedSemaphore, create_subprocess_exec, gather
from asyncio.subprocess import DEVNULL, PIPE
from calendar import monthrange
from collections.abc import Callable, Iterable, Sequence
from datetime import datetime
from glob import iglob
from os import PathLike, cpu_count
from shutil import which
from subprocess import CalledProcessError

from anyio import Path

__all__ = (
    "DEFAULT_AMOUNT_DECIMAL_PLACES",
    "find_monthly_journals",
    "find_all_journals",
    "make_datetime_range_filters",
    "filter_journals_between",
    "parse_period_start",
    "parse_period_end",
    "parse_amount",
    "format_journal_list",
    "run_hledger",
)

_SUBPROCESS_SEMAPHORE = BoundedSemaphore(cpu_count() or 4)

DEFAULT_AMOUNT_DECIMAL_PLACES = 2


async def find_monthly_journals(
    folder: PathLike[str], files: Iterable[str] | None = None
) -> Sequence[PathLike[str]]:
    """Return resolved Paths for monthly journal files under the provided folder.

    The function looks for files matching the pattern ``YYYY-MM/*.journal`` under
    the provided ``folder``. If ``files`` is supplied, those are resolved
    (strict) and returned instead. The function returns the resolved paths in
    the same order the filesystem yields them.

    Parameters
    ----------
    folder: PathLike
        PathLike pointing to the repository root or folder to search (typically the ledger
        folder).
    files: Iterable[str] | None
        Optional explicit file paths to resolve and return.

    Returns
    -------
    Sequence[PathLike]
        A sequence of resolved :class:`os.PathLike` objects.
    """
    if files:
        return await gather(*(Path(path).resolve(strict=True) for path in files))

    pattern = "**/*[0123456789][0123456789][0123456789][0123456789]-[0123456789][0123456789]/*.journal"
    return await gather(
        *(
            Path(folder, path).resolve(strict=True)
            for path in iglob(pattern, root_dir=folder, recursive=True)
        )
    )


async def find_all_journals(folder: PathLike[str]) -> Sequence[PathLike[str]]:
    """Return resolved Paths for all journal files under the provided folder.

    The function finds all ``*.journal`` files under the supplied ``folder``
    and returns the resolved :class:`os.PathLike` objects.

    Parameters
    ----------
    folder: PathLike
        PathLike pointing to the repository root or folder to search (typically the script
        folder).

    Returns
    -------
    Sequence[PathLike]
        A sequence of resolved :class:`os.PathLike` objects.
    """
    return await gather(
        *(
            Path(folder, path).resolve(strict=True)
            for path in iglob("**/*.journal", root_dir=folder, recursive=True)
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
            """Return True for any datetime when no lower bound is specified."""
            return True

    else:

        def from_filter(dt: datetime) -> bool:
            """Return True when ``dt`` is on/after the provided ``from_datetime``."""
            return from_datetime <= dt

    if to_datetime is None:

        def to_filter(dt: datetime) -> bool:
            """Return True for any datetime when no upper bound is specified."""
            return True

    else:

        def to_filter(dt: datetime) -> bool:
            """Return True when ``dt`` is on/before the provided ``to_datetime``."""
            return dt <= to_datetime

    return from_filter, to_filter


def filter_journals_between(
    journals: Iterable[PathLike[str]],
    from_datetime: datetime | None,
    to_datetime: datetime | None,
) -> Sequence[PathLike[str]]:
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
        """Return a :class:`datetime` representing the last moment of the month for ``dt``."""
        return dt.replace(
            day=monthrange(dt.year, dt.month)[1],
            hour=23,
            minute=59,
            second=59,
            microsecond=999999,
            fold=1,
        )

    ret: list[PathLike[str]] = []
    for journal in journals:
        try:
            p = Path(journal)
            to_date = datetime.fromisoformat(f"{p.parent.name}-01")
        except Exception:
            continue
        if to_filter(month_end(to_date)) and from_filter(to_date):
            ret.append(journal)
    return ret


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
        from contextlib import suppress

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
        from contextlib import suppress

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
        s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    return float(s)


def format_journal_list(
    journals: Iterable[PathLike[str]], *, max_items: int = 8
) -> str:
    """Return a compact, human-friendly multi-line representation of ``journals``.

    The representation includes a total count and the first ``max_items``
    entries formatted as ``<YYYY-MM>/<name>.journal``. When there are more
    entries than ``max_items`` the output ends with an ellipsis indicating
    how many items were omitted.

    Examples:
        12 journals
          - 2024-01/self.journal
          - 2024-02/self.alternatives.journal
          - ... (9 more)
    """
    lst = list(journals)
    count = len(lst)
    if count == 0:
        return "none"

    visible = lst[:max_items]
    lines = [f"{count} journal{'s' if count != 1 else ''}"]
    for orig in visible:
        try:
            p = Path(orig)
            label = f"{p.parent.name}/{p.name}"
        except Exception:
            label = orig
        lines.append(f"  - {label}")
    if count > max_items:
        lines.append(f"  ... ({count - max_items} more)")
    return "\n".join(lines)


async def run_hledger(
    journal: PathLike[str], *args: str, raise_on_error: bool = True, strict: bool = True
) -> tuple[str, str, int]:
    """Run `hledger --file <journal> [--strict] <*args>` and return (stdout, stderr, returncode)."""
    hledger_prog = which("hledger")
    if hledger_prog is None:
        raise FileNotFoundError("hledger executable not found in PATH")

    async with _SUBPROCESS_SEMAPHORE:
        cli = (
            hledger_prog,
            "--file",
            journal,
            *(("--strict",) if strict else ()),
            *args,
        )
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
