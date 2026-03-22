"""Small concurrency helpers."""

from collections.abc import Awaitable

from asyncer import create_task_group

"""Public symbols exported by this module."""
__all__ = ("gather_and_raise",)


async def gather_and_raise(*awaitables: Awaitable[object]) -> None:
    """Run many awaitables concurrently and raise grouped exceptions.

    This helper wraps structured concurrency task groups with exception
    gathering and converts any raised exceptions into a single :class:`BaseExceptionGroup`.

    Parameters
    ----------
    *awaitables: Awaitable[object]
        The awaitables (coroutines/futures) to run concurrently.

    Raises
    ------
    BaseExceptionGroup
        If any of the awaitables raised; the group's members will be the
        individual exceptions raised by those awaitables.
    """
    errs: list[BaseException] = []

    async def _await(a: Awaitable[object]) -> object:
        """Helper to await an awaitable and capture exceptions."""
        return await a

    try:
        async with create_task_group() as tg:
            for awaitable in awaitables:
                tg.soonify(_await)(awaitable)
    except BaseExceptionGroup as eg:
        errs.extend(eg.exceptions)
    except BaseException as e:
        errs.append(e)

    if errs:
        raise BaseExceptionGroup("One or more tasks failed", errs)
