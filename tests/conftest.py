"""Test fixtures used across the test suite.

This module provides a small factory for creating objects that emulate
`anyio.Path`-like async file objects. Tests should prefer using these
fixtures rather than re-defining ad-hoc async file classes.

Type hints:
- The factory accepts kind: "disk" or "memory" and an argument which is
  a path-like object (`os.PathLike`) for disk-backed files or an initial
  string for in-memory files.
"""

from collections.abc import Callable
from os import PathLike
from typing import Literal, Self

import pytest
from anyio import Path


@pytest.fixture
def async_file_factory() -> (
    Callable[[Literal["disk", "memory"], PathLike[str] | str], object]
):
    """Return a small factory for producing AsyncFilePath-like objects.

    Args:
        kind: Either ``"disk"`` to create an object backed by a real
            filesystem ``os.PathLike`` or ``"memory"`` to create an
            in-memory async file-like object.
        arg: For ``"disk"`` this must be a :class:`os.PathLike`; for ``"memory"`` this must be the
            initial text content (``str``).

    Returns:
        A factory callable producing objects with an ``open`` async method
        that mimics :class:`anyio.Path`'s ``open`` behaviour for tests.
    """

    class DiskAsyncFilePath:
        class AsyncFile:
            def __init__(self, path: "DiskAsyncFilePath") -> None:
                self._path = path

            async def read(self) -> str:
                return await self._path._path.read_text()

            async def write(self, data: str) -> int:
                self._path.last_written = data
                await self._path._path.write_text(data)
                return len(data)

            async def seek(self, offset: int, whence: int = 0) -> int:
                return 0

            async def truncate(self) -> None:
                return None

            async def __aenter__(self) -> Self:
                return self

            async def __aexit__(
                self,
                exc_type: type | None,
                exc: BaseException | None,
                tb: object | None,
            ) -> bool:
                return False

        def __init__(self, path: PathLike[str]) -> None:
            self._path = Path(path)
            self.last_written: str | None = None

        async def open(
            self,
            mode: str = "r+t",
            encoding: str = "UTF-8",
            errors: str = "strict",
            newline: str | None = None,
        ) -> AsyncFile:
            return self.AsyncFile(self)

    class InMemoryAsyncFilePath:
        class AsyncFile:
            def __init__(self, path: "InMemoryAsyncFilePath") -> None:
                self._path = path

            async def read(self) -> str:
                return self._path._text

            async def write(self, data: str) -> int:
                self._path.last_written = data
                self._path._text = data
                return len(data)

            async def seek(self, offset: int, whence: int = 0) -> int:
                return 0

            async def truncate(self) -> None:
                return None

            async def __aenter__(self) -> Self:
                return self

            async def __aexit__(
                self,
                exc_type: type | None,
                exc: BaseException | None,
                tb: object | None,
            ) -> bool:
                return False

        def __init__(self, text: str) -> None:
            self._text = text
            self.last_written: str | None = None

        async def open(
            self,
            mode: str = "r+t",
            encoding: str = "UTF-8",
            errors: str = "strict",
            newline: str | None = None,
        ) -> AsyncFile:
            return self.AsyncFile(self)

    def factory(kind: Literal["disk", "memory"], arg: PathLike[str] | str) -> object:
        if kind == "disk":
            if not isinstance(arg, PathLike):
                raise TypeError("disk factory requires a os.PathLike")
            return DiskAsyncFilePath(arg)
        if kind == "memory":
            if not isinstance(arg, str):
                raise TypeError("memory factory requires initial text")
            return InMemoryAsyncFilePath(arg)
        raise ValueError(kind)

    return factory
