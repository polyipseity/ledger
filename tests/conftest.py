"""Test fixtures used across the test suite.

This module provides a small factory for creating objects that emulate
`anyio.Path`-like async file objects. Tests should prefer using these
fixtures rather than re-defining ad-hoc async file classes.

Type hints:
- The factory accepts kind: "disk" or "memory" and an argument which is
  a path-like object (`os.PathLike`) for disk-backed files or an initial
  string for in-memory files.
"""

import asyncio
import runpy
import sys
from abc import ABC, abstractmethod
from collections.abc import Coroutine
from os import PathLike
from typing import Any, Literal, Protocol, Self, overload

import pytest
from anyio import Path

__all__ = (
    "AsyncFileFactory",
    "RunModuleHelper",
    "async_file_factory",
    "run_module_helper",
)


class AsyncFileBase(ABC):
    @abstractmethod
    async def read(self) -> str: ...

    @abstractmethod
    async def write(self, data: str) -> int: ...

    @abstractmethod
    async def seek(self, offset: int, whence: int = 0) -> int: ...

    @abstractmethod
    async def truncate(self) -> None: ...

    @abstractmethod
    async def __aenter__(self) -> Self: ...

    @abstractmethod
    async def __aexit__(
        self, exc_type: type | None, exc: BaseException | None, tb: object | None
    ) -> bool: ...


class AsyncPathBase(ABC):
    """Abstract base class for Async path-like objects returned by the factory."""

    last_written: str | None

    @abstractmethod
    async def open(
        self,
        mode: str = "r+t",
        encoding: str = "UTF-8",
        errors: str = "strict",
        newline: str | None = None,
    ) -> AsyncFileBase: ...


class DiskAsyncFilePathBase(AsyncPathBase, ABC):
    """ABC for disk-backed async path-like objects used by tests."""


class InMemoryAsyncFilePathBase(AsyncPathBase, ABC):
    """ABC for in-memory async path-like objects used by tests."""


class AsyncFileFactory(Protocol):
    @overload
    def __call__(self, kind: Literal["disk"], arg: PathLike[str]) -> AsyncPathBase: ...

    @overload
    def __call__(self, kind: Literal["memory"], arg: str) -> AsyncPathBase: ...

    def __call__(
        self, kind: Literal["disk", "memory"], arg: PathLike[str] | str
    ) -> AsyncPathBase: ...


@pytest.fixture
def async_file_factory() -> AsyncFileFactory:
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

    class DiskAsyncFilePath(AsyncPathBase):
        """An anyio.Path-like wrapper backed by a real filesystem path for tests."""

        class AsyncFile(AsyncFileBase):
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
        ) -> AsyncFileBase:
            """Return an :class:`AsyncFileABC` instance for the path."""
            return self.AsyncFile(self)

    class InMemoryAsyncFilePath(AsyncPathBase):
        """An in-memory anyio.Path-like wrapper for tests that keeps text in RAM."""

        class AsyncFile(AsyncFileBase):
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
        ) -> AsyncFileBase:
            """Return an :class:`AsyncFileABC` instance that manipulates in-memory text."""
            return self.AsyncFile(self)

    @overload
    def factory(kind: Literal["disk"], arg: PathLike[str]) -> AsyncPathBase: ...

    @overload
    def factory(kind: Literal["memory"], arg: str) -> AsyncPathBase: ...

    def factory(
        kind: Literal["disk", "memory"], arg: PathLike[str] | str
    ) -> AsyncPathBase:
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


class RunModuleHelper(ABC):
    """ABC representing a helper that runs a module and reports whether it ran.

    Implementations must be callable and return a dict containing a "ran"
    boolean to indicate the helper invoked the target module.
    """

    @abstractmethod
    def __call__(self, module_name: str, argv: list[str]) -> dict[str, bool]: ...


@pytest.fixture
def run_module_helper(monkeypatch: pytest.MonkeyPatch) -> RunModuleHelper:
    """Return a helper that runs a module as a script with a safe fake asyncio.run.

    The returned callable takes ``module_name`` and ``argv`` and returns a dict
    containing a ``ran`` boolean (mirroring previous tests' pattern). The
    helper sets ``sys.argv`` for the module, patches ``asyncio.run`` with a
    fake that closes the coroutine to avoid 'coroutine was never awaited'
    warnings, and clears the module from ``sys.modules`` so ``runpy`` imports
    it afresh for each invocation.
    """

    class _RunModule(RunModuleHelper):
        def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
            self._monkeypatch = monkeypatch

        def __call__(self, module_name: str, argv: list[str]) -> dict[str, bool]:
            called: dict[str, bool] = {"ran": False}

            def fake_run(coro: Coroutine[Any, Any, Any]) -> None:
                called["ran"] = True
                try:
                    coro.close()
                except Exception:
                    # If coro isn't a coroutine or close fails, ignore the error.
                    pass

            self._monkeypatch.setattr(asyncio, "run", fake_run)
            self._monkeypatch.setattr(sys, "argv", argv)

            # Ensure a fresh import context to avoid runpy-related runtime warnings
            for m in (module_name, "scripts"):
                sys.modules.pop(m, None)

            runpy.run_module(module_name, run_name="__main__")
            return called

    return _RunModule(monkeypatch)
