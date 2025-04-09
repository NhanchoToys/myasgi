from collections.abc import (
    Awaitable,
    Coroutine,
    Mapping,
    MutableMapping,
    MutableSequence,
)
from typing import Any, Callable, Literal, NotRequired, TypedDict

type CommonMapping = MutableMapping[str, Any]

type PassthroughDecorator[F: Callable[..., Any]] = Callable[[F], F]
type WrappingDecorator[**P, R] = Callable[[Callable[P, R]], Callable[P, R]]

type HostPortTuple = tuple[str, int]
type UnixSocketTuple = tuple[str, Literal[None]]
type Receive[R: Mapping[str, Any]] = Callable[[], Coroutine[Any, Any, R]]
type Send = Callable[[CommonMapping], Coroutine[Any, Any, None]]

type AsyncCallable[**P, R] = Callable[P, Awaitable[R]]
type AnyAsyncCallable = AsyncCallable[..., Any]
type RouteMapping[R] = MutableMapping[str, AsyncCallable[..., R]]


class ASGIInfo(TypedDict):
    version: str
    spec_version: str


class LifespanScope(TypedDict):
    type: Literal["lifespan"]
    asgi: ASGIInfo
    state: CommonMapping


class HTTPScope(TypedDict):
    type: Literal["http"]
    asgi: ASGIInfo
    http_version: str
    server: HostPortTuple | UnixSocketTuple
    client: HostPortTuple
    scheme: str
    method: Literal["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    root_path: str
    path: str
    raw_path: bytes
    query_string: bytes
    headers: MutableSequence[tuple[str, str]]
    state: CommonMapping


type AnyScope = LifespanScope | HTTPScope


class ReceiveLifespan(TypedDict):
    type: Literal["lifespan.startup", "lifespan.shutdown"]


class ReceiveHTTPRequest(TypedDict):
    type: Literal["http.request"]
    body: NotRequired[bytes]
    more_body: NotRequired[bool]


class ReceiveHTTPDisconnect(TypedDict):
    type: Literal["http.disconnect"]


type ReceiveHTTP = ReceiveHTTPRequest | ReceiveHTTPDisconnect
