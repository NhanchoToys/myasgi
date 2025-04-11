from collections.abc import AsyncGenerator
from typing import Any

from app import App
from app.components.http import HTTPComponent
from app.components.lifespan import LifespanComponent
from app.subroutines.http import HTMLResponse

app = App()

lifespan = app.use_component(LifespanComponent())
http = app.use_component(HTTPComponent())


@lifespan.on_context
async def my_context() -> AsyncGenerator[Any, None]:
    try:
        print("Start!")
        yield
    finally:
        print("Stop!")


# @lifespan.on_startup
# async def start() -> None:
#     print("Start!")


# @lifespan.on_shutdown
# async def stop() -> None:
#     print("Stop!")


@http.route("/teapot", get=True, post=True, put=True, delete=True)
async def teapot() -> HTMLResponse:
    resp = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>I'm a Teapot!!!</title>
        </head>
        <body>
            <h1>I'm a Teapot!!!</h1>
            <p>I've already told you I'm a teapot.</p>
        </body>
    </html>
    """
    return HTMLResponse(status=418, content=resp)
