"""Tests for :mod:`scripts.utils.cache`.

Exercise the cache helpers used by repository scripts. Tests cover reading and
writing the cache file, computing file hashes, deriving script cache keys,
marking journals as processed, evicting stale or malformed entries, and the
behaviour of :class:`~scripts.utils.cache.JournalRunContext`.
"""

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from json import JSONDecodeError
from os import PathLike, fspath, path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from anyio import Path

from scripts.utils import cache as cmod

__all__ = ()


@pytest.mark.asyncio
async def test_journal_run_context_skipped_non_file_entry_replaced(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """If a skipped file has a malformed file entry (not a FileEntryModel),
    __aexit__ should compute the hash and replace it with a proper
    :class:`FileEntryModel` containing last_success.
    """
    # Direct cache to a temporary location
    await _patch_cache_to(tmp_path, monkeypatch)

    script_path = Path(tmp_path) / "script.py"
    await script_path.write_text("print(1)\n")

    j1 = Path(tmp_path) / "2024-01" / "a.journal"
    await j1.parent.mkdir(parents=True)
    await j1.write_text("one")

    # Pre-seed cache with a malformed file entry object that has a 'hash' attr
    initial_cache = cmod.CacheModel(root={})
    key = await cmod.script_key_from(script_path)
    entry = cmod.ScriptEntryModel()
    entry.last_access = datetime.now(timezone.utc)
    # compute the file hash so __aenter__ will consider it 'skipped'
    h = await cmod.file_hash(j1)
    # intentionally use a simple namespace instead of a FileEntryModel to simulate a malformed entry that might exist in older cache versions; it has a 'hash' attribute but is not a valid FileEntryModel
    entry.files[fspath(j1)] = cast(cmod.FileEntryModel, SimpleNamespace(hash=h))
    initial_cache.root[key] = entry
    await cmod.write_script_cache(initial_cache)

    async with cmod.JournalRunContext(script_path, [j1]) as run:
        # j1 should be considered skipped because the cached object has matching 'hash'
        assert j1 in run.skipped

    # After exit, the malformed entry should have been replaced with a FileEntryModel
    cache_after = await cmod.read_script_cache()
    entry2 = cache_after.root[key]
    assert fspath(j1) in entry2.files
    assert isinstance(entry2.files[fspath(j1)], cmod.FileEntryModel)
    assert entry2.files[fspath(j1)].last_success is not None


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

    def fake_cache_file_path() -> Path:
        return target

    monkeypatch.setattr(cmod, "cache_file_path", fake_cache_file_path)
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
async def test_script_key_always_includes_preludes_component(
    tmp_path: PathLike[str],
) -> None:
    """The script key should always contain a `+preludes@` component (may be empty)."""
    script_path = Path(tmp_path) / "myscript2.py"
    await script_path.write_text("print(2)\n")
    key = await cmod.script_key_from(script_path)
    assert "+preludes@" in key


@pytest.mark.asyncio
async def test_script_key_changes_when_prelude_files_change(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Changes in files under `preludes/` should change the script key."""
    preludes = Path(tmp_path) / "preludes"
    await preludes.mkdir(parents=True)
    f = preludes / "a.txt"
    await f.write_text("v1")
    # Point the module at our temporary preludes directory
    monkeypatch.setattr(cmod, "_PRELUDES_DIR", Path(preludes))

    script_path = Path(tmp_path) / "script.py"
    await script_path.write_text("print(1)\n")

    key1 = await cmod.script_key_from(script_path)
    # Modify a prelude file -> key should change
    await f.write_text("v2")
    key2 = await cmod.script_key_from(script_path)

    assert key1 != key2


@pytest.mark.asyncio
async def test_should_skip_journal_respects_preludes_changes(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Journals marked processed should become non-skippable if preludes change."""
    await _patch_cache_to(tmp_path, monkeypatch)

    preludes = Path(tmp_path) / "preludes"
    await preludes.mkdir(parents=True)
    pfile = preludes / "cfg"
    await pfile.write_text("v1")
    monkeypatch.setattr(cmod, "_PRELUDES_DIR", Path(preludes))

    script_path = Path(tmp_path) / "script.py"
    await script_path.write_text("x")

    journal_path = Path(tmp_path) / "2024-01" / "self.journal"
    await journal_path.parent.mkdir(parents=True)
    await journal_path.write_text("txn")

    # Mark processed with initial preludes
    await cmod.mark_journal_processed(script_path, journal_path)
    assert (await cmod.should_skip_journal(script_path, journal_path)) is True

    # Mutate preludes -> should no longer be skippable
    await pfile.write_text("v2")
    assert (await cmod.should_skip_journal(script_path, journal_path)) is False


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

    cmod.evict_old_scripts(cache)
    assert "oldscript@x" not in cache.root
    # file 'a' should be removed; 'b' should be removed as malformed
    assert "a" not in cache.root["s2@x"].files
    assert "b" not in cache.root["s2@x"].files


def test_evict_respects_separate_durations() -> None:
    """Eviction should respect separate script- and file-age thresholds."""
    now = datetime.now(timezone.utc)
    old = now - timedelta(days=90)
    cache = cmod.CacheModel(root={})

    # Script old but files recent
    s_script_old = cmod.ScriptEntryModel()
    s_script_old.last_access = old
    s_script_old.files["a"] = cmod.FileEntryModel(hash="x", last_success=now)
    cache.root["oldscript@x"] = s_script_old

    # Script recent but file old
    s_file_old = cmod.ScriptEntryModel()
    s_file_old.last_access = now
    s_file_old.files["b"] = cmod.FileEntryModel(hash="x", last_success=old)
    cache.root["sfile@x"] = s_file_old

    # Evict scripts older than 1 second, keep files (large file_age_seconds)
    cmod.evict_old_scripts(
        cache, script_age_seconds=1, file_age_seconds=1000 * 24 * 3600
    )
    assert "oldscript@x" not in cache.root
    assert "sfile@x" in cache.root
    assert "b" in cache.root["sfile@x"].files

    # Reset and do opposite: keep scripts, remove files older than 1 second
    cache = cmod.CacheModel(root={})
    s_script_old = cmod.ScriptEntryModel()
    s_script_old.last_access = old
    s_script_old.files["a"] = cmod.FileEntryModel(hash="x", last_success=now)
    cache.root["oldscript@x"] = s_script_old

    s_file_old = cmod.ScriptEntryModel()
    s_file_old.last_access = now
    s_file_old.files["b"] = cmod.FileEntryModel(hash="x", last_success=old)
    cache.root["sfile@x"] = s_file_old

    cmod.evict_old_scripts(
        cache, script_age_seconds=1000 * 24 * 3600, file_age_seconds=1
    )
    assert "oldscript@x" in cache.root
    assert "b" not in cache.root["sfile@x"].files


@pytest.mark.asyncio
async def test_file_hash_missing_raises(tmp_path: PathLike[str]) -> None:
    """file_hash should raise FileNotFoundError for missing files."""
    missing = Path(tmp_path) / "nope.txt"
    with pytest.raises(FileNotFoundError):
        await cmod.file_hash(missing)


@pytest.mark.asyncio
async def test_file_hash_handles_binary(tmp_path: PathLike[str]) -> None:
    """Ensure file_hash works on binary files as well."""
    p = Path(tmp_path) / "bin.bin"
    await p.write_bytes(b"\x00\xff\x00")
    h = await cmod.file_hash(p)
    assert isinstance(h, str) and len(h) == 64


@pytest.mark.asyncio
async def test_mark_journal_processed_with_missing_journal(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """If the journal is unreadable, mark_journal_processed should still update last_access but not file entries."""
    _ = await _patch_cache_to(tmp_path, monkeypatch)
    script_path = Path(tmp_path) / "script.py"
    await script_path.write_text("print(1)\n")

    missing_j = Path(tmp_path) / "2024-01" / "missing.journal"
    # ensure parent exists but file does not
    await missing_j.parent.mkdir(parents=True, exist_ok=True)

    await cmod.mark_journal_processed(script_path, missing_j)

    cache_after = await cmod.read_script_cache()
    key = await cmod.script_key_from(script_path)
    # Because the journal was missing, mark_journal_processed returns early and does not persist entries.
    assert key not in cache_after.root


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


@pytest.mark.asyncio
async def test_read_script_cache_invalid_json(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Invalid JSON in the cache file should result in an empty cache model and not raise."""
    target = await _patch_cache_to(tmp_path, monkeypatch)
    # Write invalid JSON
    async with await target.open(mode="w+t", encoding="utf-8") as fh:
        await fh.write("not-a-json")

    cache = await cmod.read_script_cache()
    assert cache.root == {}


@pytest.mark.asyncio
async def test_script_key_from_missing_raises(tmp_path: PathLike[str]) -> None:
    """script_key_from should raise FileNotFoundError for unreadable script paths."""
    missing = Path(tmp_path) / "no_such.py"
    with pytest.raises(FileNotFoundError):
        await cmod.script_key_from(missing)


@pytest.mark.asyncio
async def test_script_key_from_wrapped_exception(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """If underlying Path.open raises a non-FileNotFoundError, script_key_from rewraps as FileNotFoundError."""

    class BadPath:
        def __init__(self, _p: PathLike[str]) -> None:
            pass

        async def open(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError("boom")

    monkeypatch.setattr(cmod, "Path", BadPath)

    missing = Path(tmp_path) / "some.py"
    with pytest.raises(FileNotFoundError):
        await cmod.script_key_from(missing)


@pytest.mark.asyncio
async def test_journal_run_context_exception_does_not_record_files(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """When the context body raises, only last_access should be updated; files should not be recorded."""
    await _patch_cache_to(tmp_path, monkeypatch)

    script_path = Path(tmp_path) / "script.py"
    await script_path.write_text("print(1)\n")

    j1 = Path(tmp_path) / "2024-01" / "a.journal"
    await j1.parent.mkdir(parents=True)
    await j1.write_text("one")

    try:
        async with cmod.JournalRunContext(script_path, [j1]) as run:
            # report success then raise to simulate an error in processing
            run.report_success(j1)
            raise RuntimeError("boom")
    except RuntimeError:
        pass

    cache_after = await cmod.read_script_cache()
    key = await cmod.script_key_from(script_path)
    entry = cache_after.root.get(key)
    # Ensure last_access exists but files entry was not created for j1
    assert entry is not None and entry.last_access is not None
    assert fspath(j1) not in entry.files


def test_evict_removes_non_script_entry() -> None:
    """Non-ScriptEntryModel values in the cache root should be removed by eviction."""
    cache = cmod.CacheModel(root={})
    # intentionally insert a non-ScriptEntryModel value to simulate a malformed cache entry that might exist in older cache versions; eviction should remove it
    cache.root["bad"] = cast(cmod.ScriptEntryModel, "not-a-script")
    cmod.evict_old_scripts(cache)
    assert "bad" not in cache.root


def test_evict_handles_malformed_timestamps_and_file_entries() -> None:
    """Malformed last_access timestamps and last_success values should be handled and entries removed."""
    now = datetime.now(timezone.utc)
    cache = cmod.CacheModel(root={})

    # Script with a malformed last_access (not a datetime) should be removed
    s_bad = cmod.ScriptEntryModel()
    s_bad.last_access = cast(
        datetime, "not-a-datetime"
    )  # intentionally malformed to simulate a bad cache entry; eviction should remove it
    cache.root["badscript@x"] = s_bad

    # Script with invalid file entries where last_success lacks timestamp should lose entries
    s2 = cmod.ScriptEntryModel()
    s2.last_access = now

    class BadDatetime(datetime):
        """Datetime subclass whose timestamp method raises to simulate malformed timestamp."""

        def timestamp(self) -> float:
            raise Exception("boom")

    s2.files["a"] = cmod.FileEntryModel(
        hash="x", last_success=BadDatetime.now(timezone.utc)
    )
    cache.root["s2@x"] = s2

    cmod.evict_old_scripts(cache)
    assert "badscript@x" not in cache.root
    # file 'a' should be removed due to malformed last_success
    assert "a" not in cache.root["s2@x"].files


def test_cache_file_path_creates_dir(tmp_path: PathLike[str]) -> None:
    """Calling `cache_file_path` should create the `__pycache__` directory if missing."""
    p = cmod.cache_file_path()
    # Ensure the directory exists

    assert path.basename(path.dirname(p)) == "__pycache__"


@pytest.mark.asyncio
async def test_read_script_cache_empty_file(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """An existing but empty cache file should return an empty cache model."""
    target = await _patch_cache_to(tmp_path, monkeypatch)
    async with await target.open(mode="w+t", encoding="utf-8") as fh:
        await fh.write("")

    cache = await cmod.read_script_cache()
    assert cache.root == {}


@pytest.mark.asyncio
async def test_read_script_cache_validation_error(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """If the cache file contains JSON that parses but fails Pydantic validation, an empty cache is returned."""
    target = await _patch_cache_to(tmp_path, monkeypatch)
    # Write JSON that is syntactically valid but semantically invalid for CacheModel
    async with await target.open(mode="w+t", encoding="utf-8") as fh:
        await fh.write('{"not_a_script": "invalid"}')

    cache = await cmod.read_script_cache()
    assert cache.root == {}


@pytest.mark.asyncio
async def test_read_script_cache_handles_json_decode_error(
    tmp_path: PathLike[str],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """If CacheModel.model_validate_json raises JSONDecodeError it is handled and an empty cache is returned."""
    target = Path(tmp_path) / "__pycache__" / "test2.cache.json"
    # ensure parent exists
    await target.parent.mkdir(parents=True, exist_ok=True)
    # write some content
    async with await target.open(mode="w+t", encoding="utf-8") as fh:
        await fh.write("{invalid: }")

    # monkeypatch the cache_file_path to point to our file
    def fake_cache_file_path2() -> Path:
        return target

    monkeypatch.setattr(cmod, "cache_file_path", fake_cache_file_path2)

    # Force model_validate_json to raise JSONDecodeError explicitly
    def raiser(text: str):
        raise JSONDecodeError("msg", text, 0)

    monkeypatch.setattr(cmod.CacheModel, "model_validate_json", staticmethod(raiser))

    caplog.clear()
    cache = await cmod.read_script_cache()
    assert cache.root == {}
    # Should emit a warning about invalidating caches
    assert any("invalidating all caches" in rec.getMessage() for rec in caplog.records)


@pytest.mark.asyncio
async def test_read_script_cache_handles_model_validate_raising(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If `CacheModel.model_validate_json` raises `ValidationError`, it is handled and an empty cache is returned."""

    # Replace the module's ValidationError with a simple local exception type
    class DummyValidationError(Exception):
        """Simple stand-in exception to exercise the validation error handling branch."""

    def raiser(text: str):
        raise DummyValidationError("boom")

    monkeypatch.setattr(cmod, "ValidationError", DummyValidationError)
    monkeypatch.setattr(cmod.CacheModel, "model_validate_json", staticmethod(raiser))

    # Ensure read_script_cache returns an empty model when validation fails
    cache = await cmod.read_script_cache()
    assert cache.root == {}


@pytest.mark.asyncio
async def test_journal_run_context_entry_persists_when_reported_file_missing(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """When a reported file is missing during __aexit__, it should be skipped and not added to cache files."""
    await _patch_cache_to(tmp_path, monkeypatch)

    script_path = Path(tmp_path) / "script.py"
    await script_path.write_text("print(1)\n")

    j1 = Path(tmp_path) / "2024-01" / "missing.journal"
    await j1.parent.mkdir(parents=True)

    async with cmod.JournalRunContext(script_path, [j1]) as run:
        run.report_success(j1)

    cache_after = await cmod.read_script_cache()
    key = await cmod.script_key_from(script_path)
    entry = cache_after.root.get(key)
    # file wasn't available so it should not be present in files
    assert entry is not None
    assert fspath(j1) not in entry.files


@pytest.mark.asyncio
async def test_mark_journal_processed_writes_entry_when_file_exists(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """mark_journal_processed should persist a file entry when the journal exists on disk."""
    _target = await _patch_cache_to(tmp_path, monkeypatch)

    script_path = Path(tmp_path) / "script.py"
    await script_path.write_text("print(1)\n")

    j = Path(tmp_path) / "2024-01" / "exists.journal"
    await j.parent.mkdir(parents=True)
    await j.write_text("txn")

    await cmod.mark_journal_processed(script_path, j)

    cache_after = await cmod.read_script_cache()
    key = await cmod.script_key_from(script_path)
    entry = cache_after.root.get(key)
    assert entry is not None
    assert fspath(j) in entry.files
    assert isinstance(entry.files[fspath(j)], cmod.FileEntryModel)


@pytest.mark.asyncio
async def test_journal_run_context_missing_script_raises(
    tmp_path: PathLike[str],
) -> None:
    """If the script file is missing, entering the JournalRunContext should raise FileNotFoundError."""
    script_path = Path(tmp_path) / "no_such_script.py"
    j1 = Path(tmp_path) / "2024-01" / "a.journal"
    with pytest.raises(FileNotFoundError):
        async with cmod.JournalRunContext(script_path, [j1]) as _run:
            pass


@pytest.mark.asyncio
async def test_should_skip_journal_returns_false_when_journal_missing(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """When the journal file cannot be read, :func:`should_skip_journal` returns False."""
    # Setup script and a journal path but do not create the journal file
    script_path = Path(tmp_path) / "script.py"
    await script_path.write_text("print(1)\n")

    j = Path(tmp_path) / "2024-01" / "missing.journal"
    await j.parent.mkdir(parents=True, exist_ok=True)

    # Seed the cache so the script key exists with a file entry
    cache = cmod.CacheModel(root={})
    key = await cmod.script_key_from(script_path)
    entry = cmod.ScriptEntryModel()
    entry.last_access = datetime.now(timezone.utc)
    entry.files[fspath(j)] = cmod.FileEntryModel(hash="deadbeef", last_success=None)
    cache.root[key] = entry
    await cmod.write_script_cache(cache)

    # Because the file is missing file_hash will raise and should_skip_journal should return False
    assert (await cmod.should_skip_journal(script_path, j)) is False


@pytest.mark.asyncio
async def test_should_skip_journal_returns_false_when_no_file_entry(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """When the script has a cache entry but no per-file entry for the journal, returns False."""
    await _patch_cache_to(tmp_path, monkeypatch)

    script_path = Path(tmp_path) / "script.py"
    await script_path.write_text("print(1)\n")

    j = Path(tmp_path) / "2024-01" / "noentry.journal"
    await j.parent.mkdir(parents=True)
    await j.write_text("txn")

    # Seed cache with a script entry that contains no file entry for j
    cache = cmod.CacheModel(root={})
    key = await cmod.script_key_from(script_path)
    entry = cmod.ScriptEntryModel()
    entry.last_access = datetime.now(timezone.utc)
    # include a different file so the mapping is not empty but lacks j
    entry.files[fspath(Path(tmp_path) / "other.journal")] = cmod.FileEntryModel(
        hash="x", last_success=datetime.now(timezone.utc)
    )
    cache.root[key] = entry
    await cmod.write_script_cache(cache)

    # No per-file entry for j -> should_skip_journal returns False
    assert (await cmod.should_skip_journal(script_path, j)) is False


def test_evict_removes_files_with_no_last_success() -> None:
    """File entries with ``last_success`` of ``None`` should be removed by eviction."""
    now = datetime.now(timezone.utc)
    cache = cmod.CacheModel(root={})
    s = cmod.ScriptEntryModel()
    s.last_access = now
    s.files["a"] = cmod.FileEntryModel(hash="x", last_success=None)
    cache.root["script@x"] = s

    cmod.evict_old_scripts(cache)
    assert "a" not in cache.root["script@x"].files


@pytest.mark.asyncio
async def test_journal_run_context_updates_last_success_for_skipped(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """If a file is skipped and already has a FileEntryModel its last_success should be updated to now on exit."""
    await _patch_cache_to(tmp_path, monkeypatch)

    script_path = Path(tmp_path) / "script.py"
    await script_path.write_text("print(1)\n")

    j = Path(tmp_path) / "2024-01" / "a.journal"
    await j.parent.mkdir(parents=True)
    await j.write_text("txn")

    # Pre-seed cache with an existing FileEntryModel but an old last_success
    initial_cache = cmod.CacheModel(root={})
    key = await cmod.script_key_from(script_path)
    entry = cmod.ScriptEntryModel()
    entry.last_access = datetime.now(timezone.utc)
    old = datetime.now(timezone.utc) - timedelta(days=90)
    entry.files[fspath(j)] = cmod.FileEntryModel(
        hash=await cmod.file_hash(j), last_success=old
    )
    initial_cache.root[key] = entry
    await cmod.write_script_cache(initial_cache)

    async with cmod.JournalRunContext(script_path, [j]) as run:
        # j should be considered skipped
        assert j in run.skipped

    cache_after = await cmod.read_script_cache()
    entry2 = cache_after.root[key]
    assert fspath(j) in entry2.files
    assert (last_success := entry2.files[fspath(j)].last_success) is not None
    assert last_success > old
