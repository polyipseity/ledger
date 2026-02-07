"""Script-level cache helpers.

This module implements the simple per-script cache used by scripts. The
cache file is placed in ``./__pycache__`` and its name is derived
from the module's filename: ``{stem}.cache.json`` (for example: ``cache.cache.json``).
"""

from asyncio import Lock
from collections.abc import Iterable, Sequence
from datetime import datetime, timezone
from hashlib import sha256
from json import JSONDecodeError
from os import PathLike, fspath, makedirs
from os.path import basename, dirname, join, splitext

from anyio import Path
from pydantic import BaseModel, Field, RootModel, ValidationError

__all__ = (
    "FileEntryModel",
    "ScriptEntryModel",
    "CacheModel",
    "JournalRunContext",
    "mark_journal_processed",
    "should_skip_journal",
    "read_script_cache",
    "write_script_cache",
    "file_hash",
    "script_key_from",
    "cache_file_path",
    "evict_old_scripts",
)


# Cache filename derived from this module's filename (e.g. "cache.cache.json").
_MODULE_STEM = splitext(basename(__file__))[0]
_SCRIPT_CACHE_NAME = f"{_MODULE_STEM}.cache.json"
_CACHE_LOCK: Lock = Lock()


# Pydantic models for typed cache -------------------------------------------
class FileEntryModel(BaseModel):
    """Per-file cache entry model.

    Attributes:
        hash: SHA256 hex digest of the file content when it was processed.
        last_success: UTC datetime of the last successful processing for this file.
    """

    hash: str | None = None
    last_success: datetime | None = None


class ScriptEntryModel(BaseModel):
    """Per-script cache entry model.

    Attributes:
        last_access: UTC datetime when the script was last run or accessed.
        files: Mapping from journal path (string) to :class:`FileEntryModel`.
    """

    last_access: datetime | None = None
    files: dict[str, FileEntryModel] = Field(default_factory=dict)


class CacheModel(RootModel[dict[str, ScriptEntryModel]]):
    """Root model mapping script keys to :class:`ScriptEntryModel`.

    Using a RootModel lets us validate the entire cache file as a mapping and
    keep a strongly-typed in-memory representation accessible as ``cache.root``.
    """

    root: dict[str, ScriptEntryModel]


def cache_file_path() -> PathLike:
    """Return the Path of the cache file in ``./__pycache__``."""
    cache_dir = join(dirname(__file__), "__pycache__")
    makedirs(cache_dir, exist_ok=True)
    return Path(join(cache_dir, _SCRIPT_CACHE_NAME))


async def read_script_cache() -> CacheModel:
    """Read and validate the cache file and return a :class:`CacheModel`.

    If the file is missing or invalid this function returns an empty cache
    instance (``CacheModel(root={})``), matching prior behaviour where an
    empty mapping was returned on read errors.
    """
    cache_path = Path(cache_file_path())
    try:
        async with await cache_path.open(mode="r+t", encoding="utf-8") as fh:
            text = await fh.read()
            if not text.strip():
                return CacheModel(root={})
            try:
                model = CacheModel.model_validate_json(text)
            except (JSONDecodeError, ValidationError):
                from logging import warning

                warning(
                    "Cache file %s is invalid (parse/validation error); invalidating all caches",
                    cache_path,
                )
                return CacheModel(root={})
            return model
    except FileNotFoundError:
        return CacheModel(root={})


async def write_script_cache(content: CacheModel) -> None:
    """Write ``content`` (a :class:`CacheModel`) to disk.

    Pydantic's `model_dump_json` will serialize nested datetimes as ISO strings
    by default, producing the same on-disk format used previously.
    """
    cache_path = Path(cache_file_path())
    # Use Pydantic's JSON serialization to produce stable ISO-formatted datetimes
    # and to ensure any future fields are serialized consistently.
    json_text = content.model_dump_json(indent=2, exclude_none=True)
    async with await cache_path.open(mode="w+t", encoding="utf-8") as fh:
        await fh.write(json_text)


async def file_hash(path: PathLike) -> str:
    """Return the SHA256 hex digest of ``path``'s current bytes."""
    async with await Path(path).open(mode="rb") as fh:
        data = await fh.read()
    return sha256(data).hexdigest()


async def script_key_from(script_id: PathLike) -> str:
    """Return a script key in the form ``<filename>@<sha256(contents)>``.

    ``script_id`` must be an :class:`os.PathLike` pointing at the invoking
    script. The file is read asynchronously; if the file cannot be read the
    function fails fast and raises :class:`FileNotFoundError`.

    Raises
    ------
    FileNotFoundError
        If ``script_id`` does not exist or cannot be opened for reading.
    """
    try:
        async with await Path(script_id).open(mode="rb") as fh:
            data = await fh.read()
    except Exception as exc:
        raise FileNotFoundError(f"script file {script_id} not readable: {exc}") from exc
    return f"{Path(script_id).name}@{sha256(data).hexdigest()}"


async def should_skip_journal(script_id: PathLike, journal: PathLike) -> bool:
    """Return True if ``journal`` can be safely skipped for ``script_id``.

    ``script_id`` must be an :class:`os.PathLike` pointing at the invoking script.
    The function compares the cached file hash against the current file hash.
    """
    async with _CACHE_LOCK:
        cache = await read_script_cache()
        key = await script_key_from(script_id)
        entry = cache.root.get(key)
        if entry is None:
            return False

        try:
            cur_hash = await file_hash(journal)
        except FileNotFoundError:
            return False

        files = entry.files
        file_entry = files.get(str(journal))
        if not file_entry:
            return False
        return file_entry.hash == cur_hash


async def mark_journal_processed(script_id: PathLike, journal: PathLike) -> None:
    """Record the journal's current content hash as processed for ``script_id``.

    This function immediately persists the change and updates the script's
    ``last_access`` timestamp.
    """
    async with _CACHE_LOCK:
        cache = await read_script_cache()
        key = await script_key_from(script_id)
        now = datetime.now(timezone.utc)
        entry = cache.root.setdefault(key, ScriptEntryModel())
        entry.last_access = now
        try:
            cur_hash = await file_hash(journal)
        except FileNotFoundError:
            return
        entry.files[str(journal)] = FileEntryModel(hash=cur_hash, last_success=now)

        evict_old_scripts(cache)
        await write_script_cache(cache)


def evict_old_scripts(cache: CacheModel, days: int = 30) -> None:
    """Evict script keys and old file entries from the cache.

    Behavior:
    - If a script's ``last_access`` is older than ``days`` the entire script entry
      (including all files) is removed.
    - Otherwise, any file whose ``last_success`` is older than ``days`` is removed
      from the script's ``files`` map.

    Modifies ``cache`` in-place.
    """
    threshold = datetime.now(timezone.utc).timestamp() - days * 24 * 3600
    for k in list(cache.root.keys()):
        entry = cache.root.get(k)
        if not isinstance(entry, ScriptEntryModel):
            del cache.root[k]
            continue

        # If last_access exists and is too old, evict entire script
        last_access = entry.last_access
        if last_access is not None:
            try:
                t = last_access.timestamp()
            except Exception:
                # Malformed timestamp; evict the script entry
                del cache.root[k]
                continue
            if t < threshold:
                del cache.root[k]
                continue

        # Evict old or malformed file entries based on last_success
        files = entry.files
        if not isinstance(files, dict):
            continue
        for f in list(files.keys()):
            f_entry = files.get(f)
            if not isinstance(f_entry, FileEntryModel):
                del files[f]
                continue
            last_success = f_entry.last_success
            if last_success is None:
                # No success timestamp -> treat as stale and remove
                del files[f]
                continue
            try:
                t = last_success.timestamp()
            except Exception:
                # Malformed timestamp -> remove file entry
                del files[f]
                continue
            if t < threshold:
                del files[f]


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
    - On exit the manager will always update the script's ``last_access``
      timestamp.
    - If the body completed successfully (no exception) it will also record any
      reported journal file hashes and update ``last_success`` for skipped files.
    - If the body raised an exception only ``last_access`` is persisted; no
      file hashes or per-file ``last_success`` timestamps are recorded.
    """

    def __init__(self, script_id: PathLike, journals: Iterable[PathLike]) -> None:
        """Create a JournalRunContext.

        Parameters:
            script_id: Path to the invoking script (used to compute a cache key).
            journals: Iterable of journal Path objects to consider for processing.

        The context will compute which journals need processing and provide
        methods to report successful processing so that the cache can be
        updated on exit.
        """
        self.script_id = script_id
        self._journals = list(journals)
        self.to_process: list[PathLike] = []
        self.skipped: list[PathLike] = []
        self._reported: set[PathLike] = set()
        self._script_key: str | None = None

    async def __aenter__(self) -> "JournalRunContext":
        """Enter the async context.

        On entry this acquires the cache lock, loads the cache, and partitions
        the provided journals into ``to_process`` (changed or new) and
        ``skipped`` (unchanged since last success) based on file hashes.
        """
        async with _CACHE_LOCK:
            cache = await read_script_cache()
            key = await script_key_from(self.script_id)
            self._script_key = key
            entry = cache.root.setdefault(key, ScriptEntryModel())
            entry.files = entry.files or {}

            for j in self._journals:
                files = entry.files
                file_entry = files.get(str(j))
                try:
                    cur_hash = await file_hash(j)
                except FileNotFoundError:
                    self.to_process.append(j)
                    continue
                if file_entry and file_entry.hash == cur_hash:
                    self.skipped.append(j)
                else:
                    self.to_process.append(j)

        return self

    def report_success(self, journal: PathLike) -> None:
        """Record that ``journal`` was successfully processed in this session."""
        if journal not in self._journals:
            raise ValueError("journal not managed by this JournalRunContext instance")
        self._reported.add(journal)

    @property
    def reported(self) -> Sequence[PathLike]:
        """Return a sorted list of :class:`os.PathLike` objects that were processed successfully.

        This property provides a convenient, read-only view over the internal
        ``_reported`` set preserving a stable ordering for display purposes.
        """
        return sorted(self._reported, key=fspath)

    async def __aexit__(
        self, exc_type: type | None, exc: BaseException | None, tb: object | None
    ) -> bool:
        """Exit the context and persist results.

        On successful exit (no exception) this updates the cache with hashes and
        per-file `last_success` timestamps for reported and skipped files. If an
        exception occurred during the context body, only the script's
        ``last_access`` is updated.

        The cache is then pruned via :func:`evict_old_scripts` and written to
        disk using :func:`write_script_cache`.
        """
        # Always update last_access so we record when the script was last run.
        async with _CACHE_LOCK:
            cache = await read_script_cache()
            key = self._script_key or await script_key_from(self.script_id)
            now = datetime.now(timezone.utc)
            entry = cache.root.setdefault(key, ScriptEntryModel())
            entry.last_access = now

            # If the body completed successfully, record processed file hashes
            # and update per-file last_success for reported and skipped files.
            if exc_type is None:
                # Record hashes and per-file last_success for files we processed
                for j in sorted(self._reported, key=fspath):
                    try:
                        h = await file_hash(j)
                    except FileNotFoundError:
                        continue
                    entry.files[str(j)] = FileEntryModel(hash=h, last_success=now)

                # Skipped files are treated as successful as well; update their last_success
                for j in sorted(self.skipped, key=fspath):
                    files = entry.files
                    f_entry = files.get(str(j))
                    if isinstance(f_entry, FileEntryModel):
                        f_entry.last_success = now
                    else:
                        try:
                            h = await file_hash(j)
                        except FileNotFoundError:
                            continue
                        files[str(j)] = FileEntryModel(hash=h, last_success=now)
            evict_old_scripts(cache)
            await write_script_cache(cache)
        return False
