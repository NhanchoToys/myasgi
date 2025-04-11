from abc import ABCMeta, abstractmethod
from collections.abc import MutableMapping
from typing import Any, TypeGuard

from app.types_ import AnyScope, AsyncCallable, Receive, Send


class Component[S: AnyScope, R: Any](metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, *args: Any, **kwds: Any) -> None:
        pass

    async def condition(self, scope: AnyScope) -> TypeGuard[S]:  # pyright: ignore[reportUnusedParameter]
        """Determine whether the component should run."""
        return True

    @abstractmethod
    async def handle(self, scope: S, receive: Receive[R], send: Send) -> None:
        """Component processor."""
        raise NotImplementedError


class RouteComponent[S: AnyScope, Recv_T: Any, Route_T: MutableMapping[str, Any], Route_R: Any](Component[S, Recv_T], metaclass=ABCMeta):
    routes: Route_T

    @abstractmethod
    def __init__(self, *args: Any, **kwds: Any) -> None:
        super().__init__(*args, **kwds)

    @abstractmethod
    async def route_dispatch(self, scope: S, receive: Receive[Recv_T], send: Send) -> Any:
        """Route dispatcher"""
        raise NotImplementedError

    @abstractmethod
    def route_install(self, route: str, target: AsyncCallable[..., Route_R], *, type_: str | None = None) -> None:
        """Install route target for specific type and route."""
        raise NotImplementedError