import asyncio
from typing import Any, Literal, overload

from app.components.base import Component
from app.components.http import HTTPComponent as HTTPComponent
from app.components.lifespan import LifespanComponent as LifespanComponent
from app.types_ import AnyScope, PassthroughDecorator, Receive, Send


class App:
    components: list[Component[Any, Any]]

    def __init__(self) -> None:
        self.components = []

    async def __call__(self, scope: AnyScope, receive: Receive[Any], send: Send) -> Any:
        async with asyncio.TaskGroup() as tg:
            for compo in self.components:
                if await compo.condition(scope):
                    _ = tg.create_task(compo.handle(scope, receive, send))

    @overload
    def use_component[T: Component[Any, Any]](self, component: T) -> T: ...

    @overload
    def use_component(
        self, component: Literal[None] = ..., *args: Any, **kwds: Any
    ) -> PassthroughDecorator[type[Component[Any, Any]]]: ...

    def use_component(
        self, component: Component[Any, Any] | None = None, *args: Any, **kwds: Any
    ) -> PassthroughDecorator[type[Component[Any, Any]]] | Component[Any, Any]:
        if component is None:

            def _use_component(
                component: type[Component[Any, Any]], /
            ) -> type[Component[Any, Any]]:
                self.components.append(component(*args, **kwds))
                return component

            return _use_component
        self.components.append(component)
        return component
