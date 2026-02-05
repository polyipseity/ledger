"""Script-level cache helpers.

This module implements the simple per-script cache used by scripts. The
cache file is placed in ``scripts/__pycache__`` and its name is derived
from the module's filename: ``{stem}.cache.json`` (for example: ``cache.cache.json``).
"""

from asyncio import Lock
from collections.abc import Iterable
from datetime import datetime, timezone
from hashlib import sha256
from json import JSONDecodeError, dumps, loads
from os import makedirs
from os.path import basename, dirname, join, splitext

from anyio import Path

# Cache filename derived from this module's filename (e.g. "cache.cache.json").
_MODULE_STEM = splitext(basename(__file__))[0]
_SCRIPT_CACHE_NAME = f"{_MODULE_STEM}.cache.json"
_CACHE_LOCK: Lock = Lock()


def _cache_file_path() -> Path:
    """Return the Path of the cache file in ``scripts/__pycache__``.

    The cache is intentionally stored in the parent package's ``__pycache__``
    directory (not in ``scripts/util/__pycache__``) to preserve the existing
    on-disk location.
    """
    cache_dir = join(dirname(__file__), "..", "__pycache__")
    makedirs(cache_dir, exist_ok=True)
    return Path(join(cache_dir, _SCRIPT_CACHE_NAME))


async def read_script_cache() -> dict:
    """Read and return the script cache dictionary.

    The cache file is located in the module's ``__pycache__`` directory and is
    managed internally. If the file does not exist an empty dict is returned.
    If the file cannot be parsed as JSON or has an unexpected structure the
    cache is considered invalid and an empty dict is returned.

    Returns
    -------
    dict
        The cache content mapped by script keys.
    """
    cache_path = _cache_file_path()
    try:
        async with await cache_path.open(mode="r+t", encoding="utf-8") as fh:
            text = await fh.read()
            if not text.strip():
                return {}
            try:
                data = loads(text)
            except JSONDecodeError:
                from logging import warning

                warning(
                    "Cache file %s is invalid (parse error); invalidating all caches",
                    cache_path,
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


async def write_script_cache(content: dict) -> None:
    """Write ``content`` to the script cache file.

    Parameters
    ----------
    content: dict
        The cache content to persist to disk.
    """
    cache_path = _cache_file_path()
    async with await cache_path.open(mode="w+t", encoding="utf-8") as fh:
        await fh.write(dumps(content, indent=2, sort_keys=True))


async def file_hash(path: Path) -> str:
    """Return the SHA256 hex digest of ``path``'s current bytes."""
    async with await path.open(mode="rb") as fh:
        data = await fh.read()
    return sha256(data).hexdigest()


async def script_key_from(script_id: Path) -> str:
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
        cache = await read_script_cache()
        key = await script_key_from(script_id)
        entry = cache.get(key)
        if entry is None:
            return False

        try:
            cur_hash = await file_hash(journal)
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
        cache = await read_script_cache()
        key = await script_key_from(script_id)
        now = datetime.now(timezone.utc).isoformat()
        entry = cache.setdefault(key, {})
        entry.setdefault("files", {})
        entry["last_access"] = now
        try:
            cur_hash = await file_hash(journal)
        except FileNotFoundError:
            return
        entry["files"][str(journal)] = {"hash": cur_hash, "last_seen": now}

    _evict_old_scripts(cache)
    await write_script_cache(cache)


def _evict_old_scripts(cache: dict, days: int = 30) -> None:
    """Evict script keys from cache whose last_access is older than ``days``.

    Modifies ``cache`` in-place.
    """
    threshold = datetime.now(timezone.utc).timestamp() - days * 24 * 3600
    for k in list(cache.keys()):
        entry = cache.get(k)
        if not isinstance(entry, dict):
            del cache[k]
            continue
        last_access = entry.get("last_access")
        if last_access is None:
            continue
        try:
            t = datetime.fromisoformat(last_access).timestamp()
        except Exception:
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
        self.script_id = script_id
        self._journals = list(journals)
        self.to_process: list[Path] = []
        self.skipped: list[Path] = []
        self._reported: set[str] = set()
        self._script_key: str | None = None

    async def __aenter__(self):
        async with _CACHE_LOCK:
            cache = await read_script_cache()
            key = await script_key_from(self.script_id)
            self._script_key = key
            now = datetime.now(timezone.utc).isoformat()
            entry = cache.setdefault(key, {})
            entry.setdefault("files", {})
            entry["last_access"] = now

            for j in self._journals:
                files = entry.get("files", {})
                file_entry = files.get(str(j))
                try:
                    cur_hash = await file_hash(j)
                except FileNotFoundError:
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

    @property
    def reported(self) -> list[Path]:
        """Return a sorted list of :class:`Path` objects that were processed successfully.

        This property provides a convenient, read-only view over the internal
        ``_reported`` set preserving a stable ordering for display purposes.
        """
        return [Path(p) for p in sorted(self._reported)]

    async def __aexit__(self, exc_type, exc, tb):
        if exc_type is None:
            async with _CACHE_LOCK:
                cache = await read_script_cache()
                key = self._script_key or await script_key_from(self.script_id)
                now = datetime.now(timezone.utc).isoformat()
                entry = cache.setdefault(key, {})
                entry.setdefault("files", {})
                entry["last_access"] = now

                for j in sorted(self._reported):
                    try:
                        h = await file_hash(Path(j))
                    except FileNotFoundError:
                        continue
                    entry["files"][j] = {"hash": h, "last_seen": now}

                _evict_old_scripts(cache)
                await write_script_cache(cache)
        return False


__all__ = (
    "JournalRunContext",
    "mark_journal_processed",
    "should_skip_journal",
    "read_script_cache",
    "write_script_cache",
    "file_hash",
    "script_key_from",
)
