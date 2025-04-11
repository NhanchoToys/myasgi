import asyncio
from collections.abc import AsyncGenerator
from typing import TypeVar

T = TypeVar('T')

async def agzip(*async_generators: AsyncGenerator[T, None]) -> AsyncGenerator[tuple[T, ...], None]:
    """
    `zip()`-like function for `AsyncGenerator`s.
    """
    iterators = [ag.__aiter__() for ag in async_generators]
    
    while True:
        try:
            results = await asyncio.gather(*[iterator.__anext__() for iterator in iterators])
            yield tuple(results)
        except StopAsyncIteration:
            break