from collections.abc import MutableMapping
from dataclasses import InitVar, dataclass, field
from http.cookies import BaseCookie
from types import TracebackType
from typing import Any, Self

from app.exceptions import ConnectionClosed
from app.types_ import CommonMapping, ReceiveHTTP, Send


class SimpleRequest:
    body: bytes
    body_parts: list[bytes]
    body_complete: bool
    done: bool
    keep_unset_body: bool = False

    def __init__(self, keep_unset_body: bool | None = None) -> None:
        self.body = b""
        self.body_parts = []
        self.body_complete = False
        self.done = False
        if keep_unset_body is not None:
            self.keep_unset_body = keep_unset_body

    def receive(self, received: ReceiveHTTP) -> bool:
        if received["type"] == "http.disconnect":
            self.done = True
            return True
            
        if "body" in received:
            self.body_parts.append(received["body"])
        elif self.keep_unset_body:
            self.body_parts.append(b"")

        if not ("more_body" in received and received["more_body"]):
            self.body = b"".join(self.body_parts)
            self.body_complete = True

        return self.body_complete or self.done


class SimpleResponse:
    send: Send
    headers: list[tuple[bytes, bytes]]
    status: int
    trailers: bool
    done: bool

    def __init__(self, send: Send) -> None:
        self.send = send
        self.headers = []
        self.status = 200
        self.trailers = False
        self.done = False

    def add_header(self, name: str, value: object) -> None:
        self.headers.append((name.lower().encode(), str(value).encode()))

    def prepare(self, status: int = 200, trailers: bool = False, headers: MutableMapping[str, str] | None = None) -> Self:
        self.status = status
        self.trailers = trailers
        if headers:
            for k, v in headers.items():
                self.add_header(k, v)
        return self

    async def start(self) -> None:
        if self.done:
            raise ConnectionClosed
        await self.send({
            "type": "http.response.start",
            "status": self.status,
            "headers": self.headers,
            "trailers": self.trailers
        })

    async def body(self, data: bytes = b"", *, done: bool = True) -> None:
        if self.done:
            raise ConnectionClosed
        await self.send({
            "type": "http.response.body",
            "body": data,
            "more_body": not done
        })
        self.done = done and not self.trailers

    async def part(self, data: bytes = b"") -> None:
        """Same as `Response.body(data, done=False)`"""
        return await self.body(data, done=False)

    async def finish(self, data: bytes = b"") -> None:
        """Same as `Response.body(data, done=True)`"""
        return await self.body(data, done=True)

    async def trail(self) -> None:
        if self.done:
            raise ConnectionClosed
        await self.send({"type": "http.response.trailers"})
        self.done = True

    async def __aenter__(self) -> Self:
        await self.start()
        return self

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None, /) -> bool | None:
        if not (self.done or exc_type):
            await self.finish()
        if exc_type and self.trailers:
            await self.trail()
        return None


@dataclass
class Response:
    status: int = 200
    body: bytes | None = None
    headers: CommonMapping = field(default_factory=dict[str, Any])
    content_type: InitVar[str | None] = None
    cookies: InitVar[BaseCookie[bytes] | None] = None

    def __post_init__(self, content_type: str | None, cookies: BaseCookie[bytes] | None) -> None:
        if self.body is not None:
            self.headers["content-length"] = len(self.body)
        if content_type is not None:
            self.headers["content-type"] = content_type
        if cookies is not None:
            self.headers["set-cookie"] = cookies.output(header="").strip()


@dataclass
class HTMLResponse(Response):
    content: InitVar[str] = ""
    encoding: InitVar[str] = "utf-8"

    def __post_init__(self, content_type: str | None, cookies: BaseCookie[bytes] | None, content: str, encoding: str) -> None:
        self.body: bytes | None = content.encode(encoding)
        return super().__post_init__("text/html", cookies)
