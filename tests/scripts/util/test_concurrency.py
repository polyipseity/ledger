"""Tests for :mod:`scripts.util.concurrency`.

Verify that :func:`scripts.util.concurrency.gather_and_raise` aggregates
exceptions raised by concurrent tasks into a :class:`BaseExceptionGroup` and
returns normally when all tasks succeed.
"""

import asyncio

import pytest

from scripts.util import concurrency

__all__ = ()


async def _ok_x(x: int) -> int:
    """A trivial coroutine that returns the given integer."""
    await asyncio.sleep(0)
    return x


async def _err_msg(msg: str) -> None:
    """A trivial coroutine that raises a RuntimeError."""
    await asyncio.sleep(0)
    raise RuntimeError(msg)


@pytest.mark.asyncio
async def test_gather_and_raise_no_error() -> None:
    """When all tasks succeed, gather_and_raise should return normally."""
    await concurrency.gather_and_raise(_ok_x(1), _ok_x(2))


@pytest.mark.asyncio
async def test_gather_and_raise_with_errors() -> None:
    """When tasks raise, a BaseExceptionGroup is raised containing them."""
    with pytest.raises(BaseExceptionGroup) as exc:
        await concurrency.gather_and_raise(_err_msg("a"), _err_msg("b"), _ok_x(1))
    # The group should contain the two runtime errors
    assert any(isinstance(e, RuntimeError) for e in exc.value.exceptions)
