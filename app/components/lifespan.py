import asyncio
from collections.abc import AsyncGenerator, Callable
from contextlib import AbstractAsyncContextManager, AbstractContextManager
from typing import Any, TypeGuard, cast, overload, override

from app.exceptions import LifespanError
from app.types_ import (
    AnyScope,
    AsyncCallable,
    LifespanScope,
    PassthroughDecorator,
    Receive,
    ReceiveLifespan,
    Send,
)

from .base import Component as _Component


async def resolve_context[T](
    *async_generators: AsyncGenerator[T, None],
) -> AsyncGenerator[tuple[T, ...], None]:
    """
    Resolve `AsyncGenerator`s context.
    """
    iterators = [ag.__aiter__() for ag in async_generators]

    while True:
        try:
            results = await asyncio.gather(
                *[iterator.__anext__() for iterator in iterators]
            )
            yield tuple(results)
        except StopAsyncIteration:
            break
    yield ()


class LifespanComponent(_Component[LifespanScope, ReceiveLifespan]):
    startups: list[AsyncCallable[[], None]]
    shutdowns: list[AsyncCallable[[], None]]
    contexts: list[tuple[str | None, Callable[[], AsyncGenerator[Any, None]]]]
    loaded_context: dict[str, Any]

    def __init__(self, *args: Any, **kwds: Any) -> None:
        super().__init__(*args, **kwds)
        self.startups = []
        self.shutdowns = []
        self.contexts = []
        self.loaded_context = {}

    @override
    async def condition(self, scope: AnyScope) -> TypeGuard[LifespanScope]:
        return scope["type"] == "lifespan"

    @override
    async def handle(
        self, scope: LifespanScope, receive: Receive[ReceiveLifespan], send: Send
    ) -> None:
        message = await receive()
        async for ctxs in resolve_context(*[ctx[1]() for ctx in self.contexts]):
            if message["type"] == "lifespan.startup":
                for fn in self.startups:
                    await fn()
                for name, val in zip((ctx[0] for ctx in self.contexts), ctxs):
                    if name is None:
                        continue
                    if name in self.loaded_context:
                        raise LifespanError(
                            f"Name {name!r} is already used by context {self.loaded_context[name]!r}."
                        )
                    self.loaded_context[name] = val
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                for fn in self.shutdowns:
                    await fn()
                await send({"type": "lifespan.shutdown.complete"})
                return
            message = await receive()

    def on_startup[Call_T: AsyncCallable[[], None]](self, fn: Call_T) -> Call_T:
        self.startups.append(fn)
        return fn

    def on_shutdown[Call_T: AsyncCallable[[], None]](self, fn: Call_T) -> Call_T:
        self.shutdowns.append(fn)
        return fn

    @overload
    def on_context(
        self, *, name: str | None = None
    ) -> PassthroughDecorator[Callable[[], AsyncGenerator[Any, None]]]: ...

    @overload
    def on_context[Ctx_T: Callable[[], AsyncGenerator[Any, None]]](
        self, fn: Ctx_T
    ) -> Ctx_T: ...

    def on_context[Ctx_T: Callable[[], AsyncGenerator[Any, None]]](
        self, fn: Ctx_T | None = None, *, name: str | None = None
    ) -> PassthroughDecorator[Ctx_T] | Ctx_T:
        if fn is None:

            def __wrap_context(fn: Ctx_T) -> Ctx_T:
                self.contexts.append((name, fn))
                return fn

            return __wrap_context
        self.contexts.append((name, fn))
        return fn

    @overload
    def add_managed_context(
        self,
        ctx: AbstractContextManager[Any, Any],
        async_: None = None,
        name: str | None = None,
    ) -> None: ...

    @overload
    def add_managed_context(
        self,
        ctx: AbstractAsyncContextManager[Any, Any],
        async_: None = None,
        name: str | None = None,
    ) -> None: ...

    @overload
    def add_managed_context(
        self, ctx: Any, async_: bool, name: str | None = None
    ) -> None: ...

    def add_managed_context(
        self,
        ctx: AbstractContextManager[Any, Any] | AbstractAsyncContextManager[Any, Any],
        async_: bool | None = None,
        name: str | None = None,
    ) -> None:
        if async_ is None:
            async_ = isinstance(ctx, AbstractAsyncContextManager)

        @self.on_context(name=name)
        async def __make_context() -> AsyncGenerator[Any, Any]:  # pyright: ignore[reportUnusedFunction]
            if async_:
                async with cast(AbstractAsyncContextManager[Any, Any], ctx) as c:
                    yield c
            else:
                with cast(AbstractContextManager[Any, Any], ctx) as c:
                    yield c

    def get_context[T](self, name: str, type_: type[T] | None = None) -> T:  # pyright: ignore[reportUnusedParameter]
        return cast(T, self.loaded_context[name])
