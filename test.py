from app import App
from app.components.http import HTTPComponent

# from app.components.lifespan import LifespanComponent
from app.subroutines.http import HTMLResponse

app = App()

# lifespan = app.use_component(LifespanComponent())
http = app.use_component(HTTPComponent())


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
