"""Path and parsing helpers for journals and dates."""

from asyncio import gather
from calendar import monthrange
from collections.abc import Iterable, Sequence
from datetime import datetime
from glob import iglob

from anyio import Path

DEFAULT_AMOUNT_DECIMAL_PLACES = 2


async def find_monthly_journals(
    folder: Path, files: Iterable[str] | None = None
) -> Sequence[Path]:
    if files:
        return await gather(*(Path(path).resolve(strict=True) for path in files))

    pattern = "**/*[0123456789][0123456789][0123456789][0123456789]-[0123456789][0123456789]/*.journal"
    return await gather(
        *(
            Path(folder.parent, path).resolve(strict=True)
            for path in iglob(pattern, root_dir=folder.parent, recursive=True)
        )
    )


async def find_all_journals(folder: Path) -> Sequence[Path]:
    return await gather(
        *(
            Path(folder.parent, path).resolve(strict=True)
            for path in iglob("**/*.journal", root_dir=folder.parent, recursive=True)
        )
    )


def make_datetime_range_filters(
    from_datetime: datetime | None, to_datetime: datetime | None
):
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


def parse_period_start(date_string: str) -> datetime:
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
    s = float_str.strip()
    s = s.replace(" ", "")
    if "." in s and "," in s:
        s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    return float(s)


def format_journal_list(journals: Iterable[Path], *, max_items: int = 8) -> str:
    lst = list(journals)
    count = len(lst)
    if count == 0:
        return "none"

    visible = lst[:max_items]
    lines = [f"{count} journal{'s' if count != 1 else ''}"]
    for p in visible:
        try:
            label = f"{p.parent.name}/{p.name}"
        except Exception:
            label = str(p)
        lines.append(f"  - {label}")
    if count > max_items:
        lines.append(f"  ... ({count - max_items} more)")
    return "\n".join(lines)
