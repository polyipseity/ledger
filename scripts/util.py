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

from asyncio import BoundedSemaphore, Lock, create_subprocess_exec, gather
from asyncio.subprocess import DEVNULL, PIPE
from calendar import monthrange
from collections.abc import Awaitable, Callable, Iterable, Sequence
from contextlib import suppress
from datetime import datetime, timezone
from glob import iglob
from hashlib import sha256
from inspect import currentframe, getframeinfo
from json import JSONDecodeError, dumps, loads
from os import cpu_count, makedirs
from os.path import basename, dirname, join, splitext
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
    "should_skip_journal",
    "mark_journal_processed",
    "JournalRunContext",
)

DEFAULT_AMOUNT_DECIMAL_PLACES = 2
"""Default number of decimal places used when scripts format monetary amounts.

Scripts that format monetary values should use this constant when constructing
format strings (for example: `f"{value:.{DEFAULT_AMOUNT_DECIMAL_PLACES}f}"`).
"""
_SUBPROCESS_SEMAPHORE = BoundedSemaphore(cpu_count() or 4)

# A simple per-script cache used to skip processing unchanged journal files.
# The cache is stored as JSON alongside compiled bytecode in ``scripts/__pycache__``.
# It maps script keys (a filename plus a script content hash) to per-journal
# metadata (file hash + last_seen timestamp).

_MODULE_STEM = splitext(basename(__file__))[0]
_SCRIPT_CACHE_NAME = f".{_MODULE_STEM}.cache.json"
_CACHE_LOCK: Lock = Lock()


def _cache_file_path() -> Path:
    """Return the Path of the cache file in the module's __pycache__ directory.

    The cache is stored in ``scripts/__pycache__/<name>.cache.json`` so
    it lives alongside compiled bytecode and does not clutter the repository
    root.
    """
    cache_dir = join(dirname(__file__), "__pycache__")

    makedirs(cache_dir, exist_ok=True)
    return Path(join(cache_dir, _SCRIPT_CACHE_NAME))


async def _read_script_cache() -> dict:
    """Read and return the script cache dict.

    The cache file is located in the module's __pycache__ directory and is
    managed internally; callers no longer need to supply a repository root.
    """
    cache_path = _cache_file_path()
    try:
        async with await cache_path.open(mode="r+t", encoding="utf-8") as fh:
            text = await fh.read()
            if not text.strip():
                return {}
            try:
                data = loads(text)
            except JSONDecodeError as exc:
                from logging import warning

                warning(
                    "Cache file %s is invalid (parse error: %s); invalidating all caches",
                    cache_path,
                    exc,
                )
                return {}
            if not isinstance(data, dict):
                from logging import warning

                warning(
                    "Cache file %s has unexpected format; invalidating all caches",
                    cache_path,
                )
                return {}
            return data
    except FileNotFoundError:
        return {}


async def _write_script_cache(content: dict) -> None:
    """Write ``content`` to the script cache file.

    The cache file lives under ``scripts/__pycache__`` so callers do not need
    to provide the repository path.
    """
    cache_path = _cache_file_path()
    async with await cache_path.open(mode="w+t", encoding="utf-8") as fh:
        await fh.write(dumps(content, indent=2, sort_keys=True))


async def _file_hash(path: Path) -> str:
    """Return the SHA256 hex digest of ``path``'s current bytes."""
    async with await path.open(mode="rb") as fh:
        data = await fh.read()
    return sha256(data).hexdigest()


async def _script_key_from(script_id: Path) -> str:
    """Return a script key in the form ``<filename>@<sha256(contents)>``.

    ``script_id`` must be an :class:`anyio.Path` pointing at the invoking
    script. The file is read asynchronously; if the file cannot be read the
    function fails fast and raises :class:`FileNotFoundError`.

    Raises
    ------
    FileNotFoundError
        If ``script_id`` does not exist or cannot be opened for reading.
    """
    try:
        async with await script_id.open(mode="rb") as fh:
            data = await fh.read()
    except Exception as exc:
        raise FileNotFoundError(f"script file {script_id} not readable: {exc}") from exc
    return f"{script_id.name}@{sha256(data).hexdigest()}"


async def should_skip_journal(script_id: Path, journal: Path) -> bool:
    """Return True if ``journal`` can be safely skipped for ``script_id``.

    ``script_id`` must be an :class:`anyio.Path` pointing at the invoking script.
    The function compares the cached file hash against the current file hash.
    """
    async with _CACHE_LOCK:
        cache = await _read_script_cache()
        key = await _script_key_from(script_id)
        entry = cache.get(key)
        if entry is None:
            return False

        try:
            cur_hash = await _file_hash(journal)
        except FileNotFoundError:
            return False

        files = entry.get("files", {})
        file_entry = files.get(str(journal))
        if not file_entry:
            return False
        return file_entry.get("hash") == cur_hash


async def mark_journal_processed(script_id: Path, journal: Path) -> None:
    """Record the journal's current content hash as processed for ``script_id``.

    This function immediately persists the change and updates the script's
    ``last_access`` timestamp.
    """
    async with _CACHE_LOCK:
        cache = await _read_script_cache()
        key = await _script_key_from(script_id)
        now = datetime.now(timezone.utc).isoformat()
        entry = cache.setdefault(key, {})
        entry.setdefault("files", {})
        entry["last_access"] = now
        try:
            cur_hash = await _file_hash(journal)
        except FileNotFoundError:
            # Nothing to mark if the file disappeared.
            return
        entry["files"][str(journal)] = {"hash": cur_hash, "last_seen": now}

    # Evict stale script keys on write
    _evict_old_scripts(cache)
    await _write_script_cache(cache)


def _evict_old_scripts(cache: dict, days: int = 30) -> None:
    """Evict script keys from cache whose last_access is older than ``days``.

    Modifies ``cache`` in-place.
    """

    threshold = datetime.now(timezone.utc).timestamp() - days * 24 * 3600
    for k in list(cache.keys()):
        entry = cache.get(k)
        if not isinstance(entry, dict):
            # Remove any non-structured entries; no legacy compatibility.
            del cache[k]
            continue
        last_access = entry.get("last_access")
        if last_access is None:
            # No last_access -> conservative: keep
            continue
        try:
            t = datetime.fromisoformat(last_access).timestamp()
        except Exception:
            # If parsing fails, evict the entry
            del cache[k]
            continue
        if t < threshold:
            del cache[k]


class JournalRunContext:
    """Async context manager to coordinate per-script journal processing.

    Usage:
        async with JournalRunContext(Path(__file__), journals) as run:
            # run.to_process contains journals that need processing
            for journal in run.to_process:
                ...process journal...
                run.report_success(journal)

    Behavior:
    - On entry the context manager checks the cache to split journals into
      ``to_process`` (need processing) and ``skipped`` (unchanged since last
      successful run).
    - Call :meth:`report_success` for each successfully processed journal.
    - On successful exit (no exception from the body) the manager will write
      the updated last_access and any reported journal file hashes.
    - If the body raises an exception no cache entries are updated.
    """

    def __init__(self, script_id: Path, journals: Iterable[Path]):
        # repo_root is no longer required; cache file is resolved internally
        self.script_id = script_id
        self._journals = list(journals)
        self.to_process: list[Path] = []
        self.skipped: list[Path] = []
        self._reported: set[str] = set()
        self._script_key: str | None = None

    async def __aenter__(self):
        async with _CACHE_LOCK:
            cache = await _read_script_cache()
            key = await _script_key_from(self.script_id)
            self._script_key = key
            # Mark last access in-memory (persist on successful exit)
            now = datetime.now(timezone.utc).isoformat()
            entry = cache.setdefault(key, {})
            entry.setdefault("files", {})
            entry["last_access"] = now

            for j in self._journals:
                files = entry.get("files", {})
                file_entry = files.get(str(j))
                try:
                    cur_hash = await _file_hash(j)
                except FileNotFoundError:
                    # If the file is missing, treat as needing processing so any
                    # missing/changed file is re-evaluated by the script.
                    self.to_process.append(j)
                    continue
                if file_entry and file_entry.get("hash") == cur_hash:
                    self.skipped.append(j)
                else:
                    self.to_process.append(j)

        return self

    def report_success(self, journal: Path) -> None:
        """Record that ``journal`` was successfully processed in this session."""
        if str(journal) not in (str(j) for j in self._journals):
            raise ValueError("journal not managed by this JournalRunContext instance")
        self._reported.add(str(journal))

    async def __aexit__(self, exc_type, exc, tb):
        # Only update the cache when the context body succeeded.
        if exc_type is None:
            async with _CACHE_LOCK:
                cache = await _read_script_cache()
                key = self._script_key or await _script_key_from(self.script_id)
                now = datetime.now(timezone.utc).isoformat()
                entry = cache.setdefault(key, {})
                entry.setdefault("files", {})
                entry["last_access"] = now

                for j in sorted(self._reported):
                    try:
                        h = await _file_hash(Path(j))
                    except FileNotFoundError:
                        continue
                    entry["files"][j] = {"hash": h, "last_seen": now}

                # Evict stale entries and persist
                _evict_old_scripts(cache)
                await _write_script_cache(cache)
        # Do not suppress exceptions.
        return False


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
    journal: Path, *args: str, raise_on_error: bool = True, strict: bool = True
) -> tuple[str, str, int]:
    """Run `hledger --file <journal> [--strict] <*args>` and return (stdout, stderr, returncode).

    If ``raise_on_error`` is True (the default), a non-zero exit status will
    raise :class:`subprocess.CalledProcessError` which includes the returncode
    and `stderr` text.

    Parameters
    ----------
    journal: Path
        The journal file passed to ``--file``.
    *args: str
        Additional arguments passed through to `hledger` (for example: ``"check"``).
    raise_on_error: bool
        Whether to raise :class:`subprocess.CalledProcessError` on non-zero exit
        (default: True).
    strict: bool
        Whether to include the ``--strict`` flag when invoking `hledger`.
        Defaults to ``True`` for existing behaviour.

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
        cli = (
            hledger_prog,
            "--file",
            str(journal),
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
    results = await gather(*awaitables, return_exceptions=True)
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
        return await gather(*(Path(path).resolve(strict=True) for path in files))

    pattern = "**/*[0123456789][0123456789][0123456789][0123456789]-[0123456789][0123456789]/*.journal"
    return await gather(
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
    return await gather(
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
