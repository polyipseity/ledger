"""Shared pytest configuration for asynchronous tests.

The AnyIO plugin is configured here; tests across the repository simply
depend on the ``anyio_backend`` fixture or use ``@pytest.mark.anyio``.
"""

from os import PathLike, fspath

import pytest
from anyio import Path

from scripts.utils.cache import CACHE_FILE_VARIABLE

"""Public API of this test configuration module (empty)."""
__all__ = ()

"""`pytest_plugins` is a special variable recognized by pytest to load fixtures from other modules."""
pytest_plugins = ("tests.test_utils",)


@pytest.fixture(autouse=True)
def isolated_run_cache(
    tmp_path: PathLike[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Point the run cache at a temporary file.

    The cache otherwise lands in ``scripts/utils/__pycache__``, so a test that
    exercises :class:`~scripts.utils.cache.JournalRunContext` would overwrite
    the cache the next real command reads.
    """
    monkeypatch.setenv(CACHE_FILE_VARIABLE, fspath(Path(tmp_path) / "cache.cache.json"))


@pytest.fixture
def anyio_backend():
    """Return the desired backend for AnyIO-based tests.

    Using a tuple with ``use_uvloop=True`` requests uvloop explicitly.
    AnyIO still handles platform differences (winloop on Windows) automatically.
    """
    return ("asyncio", {"use_uvloop": True})
