"""Tests for the async_file_factory fixture.

These tests exercise the async_file_factory helper used in other tests. They verify that:
- It creates disk-backed AnyIO Path-like file objects that operate on a filesystem path.
- It creates memory-backed file objects initialized with content strings and that track the last written content.
- The factory validates input types and kinds, raising appropriate errors for invalid usage.
"""

from os import PathLike
from typing import Literal, cast

import pytest
from anyio import Path

from tests.conftest import AsyncFileFactory, RunModuleHelper

__all__ = ()


@pytest.mark.asyncio
async def test_async_file_factory_disk_and_memory(
    async_file_factory: AsyncFileFactory, tmp_path: PathLike[str]
) -> None:
    """Verify disk-backed and memory-backed AnyIO.Path-like objects from async_file_factory behave correctly.

    Disk-backed objects should read existing file contents and persist writes to last_written.
    Memory-backed objects should initialize with a string and update last_written on write.
    """
    # Disk-backed
    file_path = Path(tmp_path) / "file.txt"
    disk = async_file_factory("disk", file_path)
    # create the backing file
    await file_path.write_text("hello")

    async with await disk.open(mode="r+t") as fh:
        content = await fh.read()
        assert content == "hello"
        await fh.write("world")
        assert disk.last_written == "world"

    # Memory-backed
    mem = async_file_factory("memory", "init")

    async with await mem.open() as fh:
        content = await fh.read()
        assert content == "init"
        await fh.write("new")
        assert mem.last_written == "new"


@pytest.mark.asyncio
async def test_async_file_factory_seek_truncate_and_context(
    async_file_factory: AsyncFileFactory, tmp_path: PathLike[str]
) -> None:
    """Verify that the fake AsyncFile's seek, truncate, and context manager methods behave as documented."""
    # Disk-backed variant
    file_path = Path(tmp_path) / "file2.txt"
    disk = async_file_factory("disk", file_path)
    await file_path.write_text("hello")

    async with await disk.open(mode="r+t") as fh:
        # seek returns 0 and truncate returns None
        res = await fh.seek(10)
        assert res == 0
        assert (await fh.truncate()) is None
        # context __aexit__ returns False; __aenter__ returned the file object above

    # Memory-backed variant
    mem = async_file_factory("memory", "abc")
    async with await mem.open() as fm:
        res = await fm.seek(2)
        assert res == 0
        assert (await fm.truncate()) is None


def test_async_file_factory_errors(async_file_factory: AsyncFileFactory) -> None:
    """Verify the factory validates inputs: wrong types raise TypeError and unknown kinds raise ValueError."""
    with pytest.raises(TypeError):
        # intentionally passing a non-string for the path to trigger the type check
        async_file_factory("disk", cast(PathLike[str], "not-a-path"))
    with pytest.raises(TypeError):
        # intentionally passing a non-string for memory content to trigger the type check
        async_file_factory("memory", cast(str, 123))
    with pytest.raises(ValueError):
        # intentionally passing an unknown kind to trigger the value check
        async_file_factory(cast(Literal["memory"], "unknown"), "x")


@pytest.mark.asyncio
async def test_run_module_helper_runs_and_handles_close_exception(
    tmp_path: PathLike[str],
    monkeypatch: pytest.MonkeyPatch,
    run_module_helper: RunModuleHelper,
) -> None:
    """Ensure run_module_helper calls patched asyncio.run and handles close exceptions."""
    # Create a module that calls asyncio.run(None) which will cause fake_run to
    # attempt to call None.close() and raise an AttributeError that's swallowed.
    mod_path = Path(tmp_path) / "mod_run_close.py"
    await mod_path.write_text("""import asyncio
asyncio.run(None)
""")
    monkeypatch.syspath_prepend(tmp_path)  # type: ignore[reportUnknownMemberType]

    ran = run_module_helper("mod_run_close", ["mod_run_close"])
    assert ran["ran"] is True


@pytest.mark.asyncio
async def test_run_module_helper_sets_sys_argv_and_runs_module(
    tmp_path: PathLike[str],
    monkeypatch: pytest.MonkeyPatch,
    run_module_helper: RunModuleHelper,
) -> None:
    """Verify the helper sets sys.argv for the module and runs it afresh each time."""
    mod_path = Path(tmp_path) / "mod_run_args.py"
    await mod_path.write_text("""import sys, asyncio, pathlib
p = pathlib.Path(__file__).with_suffix('.argv')
p.write_text(' '.join(sys.argv))
asyncio.run(None)
""")

    monkeypatch.syspath_prepend(tmp_path)  # type: ignore[reportUnknownMemberType]

    ran = run_module_helper("mod_run_args", ["mod_run_args", "A", "B"])
    assert ran["ran"] is True

    # The module should have written its argv file in the same directory
    argv_file = Path(tmp_path) / "mod_run_args.argv"
    assert await argv_file.exists()
    assert await argv_file.read_text() == "mod_run_args A B"

    # Run again with different args to ensure fresh import and that argv is updated
    ran2 = run_module_helper("mod_run_args", ["mod_run_args", "X"])
    assert ran2["ran"] is True
    assert await argv_file.read_text() == "mod_run_args X"
