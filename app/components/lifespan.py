from collections.abc import AsyncGenerator, Callable
from typing import Any, TypeGuard, override

from app.subroutines.asyncutils import agzip
from app.types_ import (
    AnyScope,
    AsyncCallable,
    LifespanScope,
    Receive,
    ReceiveLifespan,
    Send,
)

from .base import Component as _Component


class LifespanComponent(_Component[LifespanScope, ReceiveLifespan]):
    startups: list[AsyncCallable[[], None]]
    shutdowns: list[AsyncCallable[[], None]]
    contexts: list[Callable[[], AsyncGenerator[Any, None]]]

    def __init__(self, *args: Any, **kwds: Any) -> None:
        super().__init__(*args, **kwds)
        self.startups = []
        self.shutdowns = []
        self.contexts = []

    @override
    async def condition(self, scope: AnyScope) -> TypeGuard[LifespanScope]:
        return scope["type"] == "lifespan"

    @override
    async def handle(
        self, scope: LifespanScope, receive: Receive[ReceiveLifespan], send: Send
    ) -> None:
        message = await receive()
        async for _ in agzip(*[ctx() for ctx in self.contexts]):
            if message["type"] == "lifespan.startup":
                for fn in self.startups:
                    await fn()
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

    def on_context[Ctx_T: Callable[[], AsyncGenerator[Any, None]]](self, fn: Ctx_T) -> Ctx_T:
        self.contexts.append(fn)
        return fn
