"""Journal discovery, date parsing, and period resolution helpers."""

from calendar import monthrange
from collections.abc import Callable, Iterable, Sequence
from contextlib import suppress
from datetime import datetime
from glob import iglob
from os import PathLike, fspath
from subprocess import run

from anyio import Path
from asyncer import SoonValue, create_task_group

from .files import get_script_folder
from .hledger import MONTH_PATTERN, first_line, run_hledger

"""Public symbols exported by this module."""
__all__ = (
    "DEFAULT_AMOUNT_DECIMAL_PLACES",
    "find_monthly_journals",
    "find_all_journals",
    "make_datetime_range_filters",
    "filter_journals_between",
    "parse_period_start",
    "parse_period_end",
    "resolve_now_month",
    "resolve_period",
    "parse_amount",
    "format_journal_list",
    "run_hledger",
)

"""Default number of decimal places for amount formatting in journal output."""
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
        resolved: list[SoonValue[Path]] = []
        async with create_task_group() as tg:
            for path in files:
                resolved.append(tg.soonify(Path(path).resolve)(strict=True))
        return tuple(r.value for r in resolved)

    pattern = "**/*[0123456789][0123456789][0123456789][0123456789]-[0123456789][0123456789]/*.journal"
    resolved = []
    async with create_task_group() as tg:
        for path in iglob(pattern, root_dir=folder, recursive=True):
            resolved.append(tg.soonify(Path(folder, path).resolve)(strict=True))
    return tuple(r.value for r in resolved)


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
    resolved: list[SoonValue[Path]] = []
    async with create_task_group() as tg:
        for path in iglob("**/*.journal", root_dir=folder, recursive=True):
            resolved.append(tg.soonify(Path(folder, path).resolve)(strict=True))
    return tuple(r.value for r in resolved)


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


def resolve_now_month(explicit: str | None) -> str:
    """Return the ``YYYY-MM`` month separating closed months from future ones.

    An explicit value wins after checking that it starts with a four-digit
    year, a dash, and a two-digit month, and is truncated to those seven
    characters. Without one, the committer date of the last commit supplies the
    month, read from the repository root.

    Args:
        explicit: The requested month, or ``None`` to derive it.

    Raises:
        ValueError: When ``explicit`` does not start with a ``YYYY-MM`` prefix.
        RuntimeError: When git is missing, exits non-zero, or prints something
            that does not start with an ISO date, since there is then no month
            to classify the journals against.
    """
    if explicit is not None:
        month = explicit[:7]
        if MONTH_PATTERN.fullmatch(month) is None:
            raise ValueError(f"not a year-month prefix: {explicit!r}")
        return month

    root = fspath(get_script_folder(depth=2))
    try:
        completed = run(
            ("git", "log", "-1", "--format=%cI"),
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise RuntimeError(
            f"cannot determine the current month: git failed to start in {root}: {exc}"
        ) from exc
    if completed.returncode != 0:
        raise RuntimeError(
            "cannot determine the current month: "
            f"git log exited {completed.returncode}: {first_line(completed.stderr)}"
        )
    month = completed.stdout.strip()[:7]
    if MONTH_PATTERN.fullmatch(month) is None:
        raise RuntimeError(
            "cannot determine the current month: git log printed no commit date "
            f"in {root}: {completed.stdout.strip()!r}"
        )
    return month


def resolve_period(period: str | None) -> str | None:
    """Return ``period`` normalised to the ``YYYY-MM`` month it names.

    The value goes through :func:`parse_period_start`, so it is also rejected
    when no calendar month carries that number, and it must round-trip to the
    ``YYYY-MM`` prefix it was read from, so a bare ``YYYY`` is rejected rather
    than widened to January.

    Args:
        period: The requested month, or ``None`` for every month.

    Returns:
        The month to filter on, or ``None`` when ``period`` is absent.

    Raises:
        ValueError: When ``period`` is not a ``YYYY-MM`` month, because a typo
            would otherwise select no journal at all and report a clean chain.
    """
    if period is None:
        return None
    month = period[:7]
    try:
        start = parse_period_start(period)
    except ValueError as exc:
        raise ValueError(f"--period {period!r} is not a YYYY-MM month") from exc
    if (
        MONTH_PATTERN.fullmatch(month) is None
        or f"{start.year:04d}-{start.month:02d}" != month
    ):
        raise ValueError(f"--period {period!r} is not a YYYY-MM month")
    return month


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
