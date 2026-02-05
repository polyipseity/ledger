"""Small concurrency helpers."""

from asyncio import gather
from collections.abc import Awaitable

__all__ = ("gather_and_raise",)


async def gather_and_raise(*awaitables: Awaitable[object]) -> None:
    """Run many awaitables concurrently and raise grouped exceptions.

    This helper wraps :func:`asyncio.gather(..., return_exceptions=True)` and
    converts any returned exceptions into a single :class:`BaseExceptionGroup`.

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
    results = await gather(*awaitables, return_exceptions=True)
    errs = tuple(err for err in results if isinstance(err, BaseException))
    if errs:
        raise BaseExceptionGroup("One or more tasks failed", errs)
