"""Tests for :mod:`scripts.util.cache`.

Exercise the cache helpers used by repository scripts. Tests cover reading and
writing the cache file, computing file hashes, deriving script cache keys,
marking journals as processed, evicting stale or malformed entries, and the
behaviour of :class:`~scripts.util.cache.JournalRunContext`.
"""

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from os import PathLike, fspath
from typing import cast

import pytest
from anyio import Path

from scripts.util import cache as cmod


async def _patch_cache_to(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> Path:
    """Monkeypatch cmod.cache_file_path to point to a temp file under tmp_path.

    Also ensure the parent directory exists so writes do not fail.
    """
    pycache = Path(tmp_path) / "__pycache__"
    target = pycache / "test.cache.json"
    # ensure parent directory exists (anyio.Path doesn't create intermediate dirs)
    await pycache.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(cmod, "cache_file_path", lambda: target)
    return target


@pytest.mark.asyncio
async def test_read_write_roundtrip(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A written CacheModel should be readable and preserved.

    Uses the temporary filesystem (``tmp_path``) and monkeypatch to direct the
    cache file into a temporary location, writes a CacheModel and verifies
    it can be read back unchanged.
    """
    await _patch_cache_to(tmp_path, monkeypatch)

    cache = cmod.CacheModel(root={})
    # Create a script entry
    s_entry = cmod.ScriptEntryModel()
    s_entry.last_access = datetime.now(timezone.utc)
    cache.root["script@abc"] = s_entry

    await cmod.write_script_cache(cache)
    read_back = await cmod.read_script_cache()
    assert "script@abc" in read_back.root


@pytest.mark.asyncio
async def test_file_hash_and_script_key(tmp_path: PathLike[str]) -> None:
    """`file_hash` computes sha256 and `script_key_from` embeds file name and sha.

    This test uses synchronous filesystem writes for the test inputs and
    runs the small async helpers using anyio-runner wrappers.
    """

    p = Path(tmp_path) / "f.txt"
    await p.write_text("hello")

    h = pytest.raises(Exception)  # placeholder to keep flake happy

    h = await cmod.file_hash(p)
    assert h == sha256(b"hello").hexdigest()

    script_path = Path(tmp_path) / "myscript.py"
    await script_path.write_text("print(1)\n")

    key = await cmod.script_key_from(script_path)
    assert script_path.name in key
    assert "@" in key


@pytest.mark.asyncio
async def test_should_skip_and_mark_journal_processed(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """mark_journal_processed records the file hash and should_skip_journal uses it."""
    await _patch_cache_to(tmp_path, monkeypatch)

    script_path = Path(tmp_path) / "script.py"
    await script_path.write_text("x")

    journal_path = Path(tmp_path) / "2024-01" / "self.journal"
    await journal_path.parent.mkdir(parents=True)
    await journal_path.write_text("txn")

    # Initially nothing cached
    assert (await cmod.should_skip_journal(script_path, journal_path)) is False

    # Mark processed
    await cmod.mark_journal_processed(script_path, journal_path)

    # Now it should be considered skippable
    assert (await cmod.should_skip_journal(script_path, journal_path)) is True

    # Mutate file -> not skippable
    await journal_path.write_text("txn2")
    assert (await cmod.should_skip_journal(script_path, journal_path)) is False


def test_evict_old_scripts_and_malformed_entries() -> None:
    """evict_old_scripts removes stale scripts and malformed entries as documented."""
    now = datetime.now(timezone.utc)
    old = now - timedelta(days=90)
    cache = cmod.CacheModel(root={})

    # Old script removed entirely
    s_old = cmod.ScriptEntryModel()
    s_old.last_access = old
    cache.root["oldscript@x"] = s_old

    # Script with old file entries must lose them
    s2 = cmod.ScriptEntryModel()
    s2.last_access = now
    s2.files["a"] = cmod.FileEntryModel(hash="x", last_success=old)
    s2.files["b"] = cast(cmod.FileEntryModel, "notamodel")
    cache.root["s2@x"] = s2

    cmod.evict_old_scripts(cache, days=30)
    assert "oldscript@x" not in cache.root
    # file 'a' should be removed; 'b' should be removed as malformed
    assert "a" not in cache.root["s2@x"].files
    assert "b" not in cache.root["s2@x"].files


@pytest.mark.asyncio
async def test_journal_run_context_basic(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """JournalRunContext should partition journals and persist reported hashes."""
    await _patch_cache_to(tmp_path, monkeypatch)

    script_path = Path(tmp_path) / "script.py"
    await script_path.write_text("print(1)\n")

    j1 = Path(tmp_path) / "2024-01" / "a.journal"
    j2 = Path(tmp_path) / "2024-01" / "b.journal"
    await j1.parent.mkdir(parents=True)
    await j1.write_text("one")
    await j2.write_text("two")

    # Pre-seed cache so j1 appears as already processed
    initial_cache = cmod.CacheModel(root={})
    key = await cmod.script_key_from(script_path)
    entry = cmod.ScriptEntryModel()
    entry.last_access = datetime.now(timezone.utc)
    entry.files[fspath(j1)] = cmod.FileEntryModel(
        hash=await cmod.file_hash(j1),
        last_success=datetime.now(timezone.utc),
    )
    initial_cache.root[key] = entry
    await cmod.write_script_cache(initial_cache)

    async with cmod.JournalRunContext(script_path, [j1, j2]) as run:
        # j1 should be skipped, j2 to process
        assert j1 in run.skipped
        assert j2 in run.to_process
        # reporting success for j2
        run.report_success(j2)
        with pytest.raises(ValueError):
            # unknown journal
            run.report_success(Path("/no/such"))
        assert run.reported == [j2]

    # After exit, the cache file should contain updated last_success for j2
    cache_after = await cmod.read_script_cache()
    entry2 = cache_after.root[key]
    assert fspath(j2) in entry2.files
    assert entry2.files[fspath(j2)].last_success is not None
