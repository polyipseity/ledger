"""Script-level cache helpers.

This module implements the simple per-script cache previously embedded in
``scripts.util``. The cache file remains in ``scripts/__pycache__/.util.cache.json``
so existing on-disk behaviour is unchanged.
"""

from asyncio import Lock
from datetime import datetime, timezone
from hashlib import sha256
from json import JSONDecodeError, dumps, loads
from os import makedirs
from os.path import dirname, join

from anyio import Path

# Keep the original cache filename stem "util" so on-disk location does not
# change after the refactor.
_MODULE_STEM = "util"
_SCRIPT_CACHE_NAME = f".{_MODULE_STEM}.cache.json"
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
    cache_path = _cache_file_path()
    async with await cache_path.open(mode="w+t", encoding="utf-8") as fh:
        await fh.write(dumps(content, indent=2, sort_keys=True))


async def file_hash(path: Path) -> str:
    async with await path.open(mode="rb") as fh:
        data = await fh.read()
    return sha256(data).hexdigest()


async def script_key_from(script_id: Path) -> str:
    try:
        async with await script_id.open(mode="rb") as fh:
            data = await fh.read()
    except Exception as exc:
        raise FileNotFoundError(f"script file {script_id} not readable: {exc}") from exc
    return f"{script_id.name}@{sha256(data).hexdigest()}"


async def should_skip_journal(script_id: Path, journal: Path) -> bool:
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
