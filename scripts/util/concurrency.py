"""Small concurrency helpers."""

from asyncio import gather
from typing import Awaitable


async def gather_and_raise(*awaitables: Awaitable[object]) -> None:
    results = await gather(*awaitables, return_exceptions=True)
    errs = tuple(err for err in results if isinstance(err, BaseException))
    if errs:
        raise BaseExceptionGroup("One or more tasks failed", errs)
