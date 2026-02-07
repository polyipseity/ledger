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
        """An anyio.Path-like wrapper backed by a real filesystem path for tests."""

        class AsyncFile:
            """A minimal async file object that wraps a real file on disk."""

            def __init__(self, path: "DiskAsyncFilePath") -> None:
                """Store a reference to the parent DiskAsyncFilePath."""
                self._path = path

            async def read(self) -> str:
                """Read and return the file's text content asynchronously."""
                return await self._path._path.read_text()

            async def write(self, data: str) -> int:
                """Write ``data`` to the backing file and return length written."""
                self._path.last_written = data
                await self._path._path.write_text(data)
                return len(data)

            async def seek(self, offset: int, whence: int = 0) -> int:
                """No-op seek implementation for tests; returns 0."""
                return 0

            async def truncate(self) -> None:
                """No-op truncate implementation for tests."""
                return None

            async def __aenter__(self) -> Self:
                """Async context manager entry: returns the file object."""
                return self

            async def __aexit__(
                self,
                exc_type: type | None,
                exc: BaseException | None,
                tb: object | None,
            ) -> bool:
                """Async context manager exit: no special cleanup performed."""
                return False

        def __init__(self, path: PathLike[str]) -> None:
            """Initialize with a real filesystem path for disk-backed tests."""
            self._path = Path(path)
            self.last_written: str | None = None

        async def open(
            self,
            mode: str = "r+t",
            encoding: str = "UTF-8",
            errors: str = "strict",
            newline: str | None = None,
        ) -> AsyncFile:
            """Return an :class:`AsyncFile` instance for the path."""
            return self.AsyncFile(self)

    class InMemoryAsyncFilePath:
        """An in-memory anyio.Path-like wrapper for tests that keeps text in RAM."""

        class AsyncFile:
            """A minimal async file object that operates on in-memory text."""

            def __init__(self, path: "InMemoryAsyncFilePath") -> None:
                """Store a reference to the owning InMemoryAsyncFilePath."""
                self._path = path

            async def read(self) -> str:
                """Return the current in-memory text contents."""
                return self._path._text

            async def write(self, data: str) -> int:
                """Overwrite the in-memory text and return the number of bytes written."""
                self._path.last_written = data
                self._path._text = data
                return len(data)

            async def seek(self, offset: int, whence: int = 0) -> int:
                """No-op seek implementation for in-memory file used in tests."""
                return 0

            async def truncate(self) -> None:
                """No-op truncate implementation for in-memory file used in tests."""
                return None

            async def __aenter__(self) -> Self:
                """Async context manager entry: returns the file object."""
                return self

            async def __aexit__(
                self,
                exc_type: type | None,
                exc: BaseException | None,
                tb: object | None,
            ) -> bool:
                """Async context manager exit: no special cleanup performed."""
                return False

        def __init__(self, text: str) -> None:
            """Initialize an in-memory path object with initial text content."""
            self._text = text
            self.last_written: str | None = None

        async def open(
            self,
            mode: str = "r+t",
            encoding: str = "UTF-8",
            errors: str = "strict",
            newline: str | None = None,
        ) -> AsyncFile:
            """Return an :class:`AsyncFile` instance that manipulates in-memory text."""
            return self.AsyncFile(self)

    def factory(kind: Literal["disk", "memory"], arg: PathLike[str] | str) -> object:
        """Factory for creating test-friendly anyio.Path-like objects.

        The factory supports two kinds:
        - ``"disk"``: returns a disk-backed Path-like wrapper and requires
          ``arg`` to be an :class:`os.PathLike`.
        - ``"memory"``: returns an in-memory Path-like wrapper and requires
          ``arg`` to be an initial text string.

        Args:
            kind: One of ``"disk"`` or ``"memory"``.
            arg: Path-like object for disk-backed files or initial text for memory-backed files.

        Returns:
            An object implementing an ``open`` async method suitable for use in tests.
        """
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
