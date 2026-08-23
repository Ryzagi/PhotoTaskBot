"""ASGI middleware that HMAC-verifies /internal/* requests.

This MUST be middleware, not a FastAPI dependency: FastAPI consumes the request
body when it parses Form()/File() params, so a dependency calling
`request.body()` afterwards raises "Stream consumed" (only JSON endpoints, which
cache the body, happened to work). Here we read the raw body once — before any
parsing — verify the HMAC over (method, path, body), then replay the buffered
body to the downstream app so the endpoint can still read its form/json.
"""

from __future__ import annotations

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from bot.auth import internal as internal_auth
from bot.schemas.errors import make as make_error

_PREFIX = "/internal"


class InternalAuthMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not scope.get("path", "").startswith(_PREFIX):
            await self.app(scope, receive, send)
            return

        # Buffer the entire request body.
        body = b""
        more = True
        while more:
            message: Message = await receive()
            if message["type"] == "http.request":
                body += message.get("body", b"")
                more = message.get("more_body", False)
            else:  # http.disconnect
                more = False

        headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope.get("headers", [])}
        header = headers.get("x-internal-auth", "")
        if not header:
            await self._deny(scope, receive, send, "missing internal auth")
            return
        try:
            internal_auth.verify(header, scope["method"], scope["path"], body)
        except internal_auth.InternalAuthError as e:
            await self._deny(scope, receive, send, str(e))
            return

        # Replay the buffered body so Form()/File()/json parsing downstream works.
        replayed = False

        async def receive_replay() -> Message:
            nonlocal replayed
            if not replayed:
                replayed = True
                return {"type": "http.request", "body": body, "more_body": False}
            return {"type": "http.disconnect"}

        await self.app(scope, receive_replay, send)

    async def _deny(self, scope: Scope, receive: Receive, send: Send, detail: str) -> None:
        await JSONResponse(make_error("forbidden", detail), status_code=403)(scope, receive, send)
