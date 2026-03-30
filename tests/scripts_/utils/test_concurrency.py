"""Tests for :mod:`scripts.utils.concurrency`.

Verify that :func:`scripts.utils.concurrency.gather_and_raise` aggregates
exceptions raised by concurrent tasks into a :class:`BaseExceptionGroup` and
returns normally when all tasks succeed.
"""

from subprocess import CalledProcessError

import pytest
from anyio import sleep

from scripts.utils import concurrency

"""Public symbols exported by this module (none)."""
__all__ = ()


async def _ok_x(x: int) -> int:
    """A trivial coroutine that returns the given integer."""
    await sleep(0)
    return x


async def _err_msg(msg: str) -> None:
    """A trivial coroutine that raises a RuntimeError."""
    await sleep(0)
    raise RuntimeError(msg)


async def _err_called_process(stderr: str) -> None:
    """Raise a :class:`CalledProcessError` after yielding control once."""
    await sleep(0)
    raise CalledProcessError(2, ["hledger", "check"], output="", stderr=stderr)


@pytest.mark.anyio
async def test_gather_and_raise_no_error() -> None:
    """When all tasks succeed, gather_and_raise should return normally."""
    await concurrency.gather_and_raise(_ok_x(1), _ok_x(2))


@pytest.mark.anyio
async def test_gather_and_raise_with_errors() -> None:
    """When tasks raise, a BaseExceptionGroup is raised containing them."""
    with pytest.raises(BaseExceptionGroup) as exc:
        await concurrency.gather_and_raise(_err_msg("a"), _err_msg("b"), _ok_x(1))
    # The group should contain the two runtime errors
    assert any(isinstance(e, RuntimeError) for e in exc.value.exceptions)


@pytest.mark.anyio
async def test_gather_and_raise_includes_called_process_details() -> None:
    """CalledProcessError summaries should include stderr details in group message."""
    with pytest.raises(BaseExceptionGroup) as exc:
        await concurrency.gather_and_raise(_err_called_process("parse failure"))

    msg = str(exc.value)
    assert "Command ['hledger', 'check'] failed with exit code 2." in msg
    assert "stderr: parse failure" in msg
