from typing import TypeGuard, override

from app.types_ import AnyScope, LifespanScope, Receive, ReceiveLifespan, Send

from .base import Component as _Component


class LifespanComponent(_Component[LifespanScope, ReceiveLifespan]):
    @override
    async def condition(self, scope: AnyScope) -> TypeGuard[LifespanScope]:
        return scope["type"] == "lifespan"

    @override
    async def handle(self, scope: LifespanScope, receive: Receive[ReceiveLifespan], send: Send) -> None:
        while True:
            message = await receive()
            if message['type'] == 'lifespan.startup':
                ... # Do some startup here!
                print("Startup...")
                await send({'type': 'lifespan.startup.complete'})
            elif message['type'] == 'lifespan.shutdown':
                ... # Do some shutdown here!
                print("Shutdown...")
                await send({'type': 'lifespan.shutdown.complete'})
                return