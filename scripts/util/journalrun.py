"""Journal processing coordination context manager."""

from datetime import datetime, timezone
from typing import Iterable

from anyio import Path

from .cache import (  # type: ignore
    _CACHE_LOCK,
    _evict_old_scripts,
    file_hash,
    read_script_cache,
    script_key_from,
    write_script_cache,
)


class JournalRunContext:
    """Async context manager to coordinate per-script journal processing.

    See the original :class:`JournalRunContext` in ``scripts.util`` for
    full behaviour and usage examples.
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
        if str(journal) not in (str(j) for j in self._journals):
            raise ValueError("journal not managed by this JournalRunContext instance")
        self._reported.add(str(journal))

    @property
    def reported(self) -> list[Path]:
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
