from typing import TypeGuard, override

from app.subroutines.http import Response, SimpleRequest, SimpleResponse
from app.types_ import (
    AnyScope,
    AsyncCallable,
    HTTPScope,
    PassthroughDecorator,
    Receive,
    ReceiveHTTP,
    RouteMapping,
    Send,
)

from .base import RouteComponent as _RouteComponent


class HTTPComponent(
    _RouteComponent[HTTPScope, ReceiveHTTP, dict[str, RouteMapping[Response]], Response]
):
    routes: dict[str, RouteMapping[Response]]

    def __init__(self) -> None:
        self.routes = {}
        super().__init__()

    @override
    async def condition(self, scope: AnyScope) -> TypeGuard[HTTPScope]:
        return scope["type"] == "http"

    @override
    async def handle(
        self, scope: HTTPScope, receive: Receive[ReceiveHTTP], send: Send
    ) -> None:
        req = SimpleRequest()
        while not req.receive(await receive()):
            pass

        print(scope, req.body)
        resp = await self.route_dispatch(scope, receive, send)
        if resp is None:
            resp = Response(status=404, body=b"404 Not Found\n")

        async with SimpleResponse(send).prepare(
            resp.status, headers=resp.headers
        ) as rsp:
            await rsp.finish(resp.body if resp.body is not None else b"")

        return None

    @override
    async def route_dispatch(
        self, scope: HTTPScope, receive: Receive[ReceiveHTTP], send: Send
    ) -> Response | None:
        for k, callee in self.routes[scope["method"].upper()].items():
            if scope["path"] == k:  # temporary impl.
                return await callee()

    @override
    def route_install(self, route: str, target: AsyncCallable[..., Response], *, type_: str | None = None) -> None:
        """Install route target for specific type and route."""
        if type_ is None:
            raise ValueError("Route type `type_` is unset.")
        self.routes.setdefault(type_, {})[route] = target

    def route[T: AsyncCallable[..., Response]](
        self,
        route: str,
        *,
        get: bool = False,
        post: bool = False,
        put: bool = False,
        delete: bool = False,
        head: bool = False,
    ) -> PassthroughDecorator[T]:
        def __wrap_route(fn: T) -> T:
            if get:
                self.route_install(route, fn, type_="GET")
            if post:
                self.route_install(route, fn, type_="POST")
            if put:
                self.route_install(route, fn, type_="PUT")
            if delete:
                self.route_install(route, fn, type_="DELETE")
            if head:
                self.route_install(route, fn, type_="HEAD")
            return fn

        return __wrap_route

    def get[T: AsyncCallable[..., Response]](
        self, route: str
    ) -> PassthroughDecorator[T]:
        return self.route(route, get=True)

    def post[T: AsyncCallable[..., Response]](
        self, route: str
    ) -> PassthroughDecorator[T]:
        return self.route(route, post=True)

    def put[T: AsyncCallable[..., Response]](
        self, route: str
    ) -> PassthroughDecorator[T]:
        return self.route(route, put=True)

    def delete[T: AsyncCallable[..., Response]](
        self, route: str
    ) -> PassthroughDecorator[T]:
        return self.route(route, delete=True)
