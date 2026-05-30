"""HMAC-signing HTTP client used by the Telegram bot to call /internal/*.

Drop-in replacement for the bare `aiohttp.ClientSession().post(url, …)` pattern
the bot currently uses. Every request gets a fresh `X-Internal-Auth` header
signed with INTERNAL_AUTH_SECRET; the backend verifies it before the route
handler runs (see bot.auth.dependencies.verify_internal).

Multipart bodies are constructed by hand so that signing has predictable bytes
to hash — aiohttp's streaming FormData would force us to buffer it back
together anyway.

Usage:

    from bot.internal_client import InternalClient
    from bot.constants import NETWORK, INTERNAL_SOLVE_IMAGE_ENDPOINT

    async with InternalClient(base=f"http://{NETWORK}:8000") as client:
        status, body = await client.post_multipart(
            INTERNAL_SOLVE_IMAGE_ENDPOINT,
            fields={"telegram_user_id": str(user.id)},
            file=("file", "task.jpg", file_bytes, "image/jpeg"),
        )
"""

from __future__ import annotations

import json as _json
import secrets
from typing import Any

import aiohttp

from bot.auth import internal as internal_auth


class InternalClient:
    """Thin async-context HTTP client. Every request is HMAC-signed."""

    def __init__(self, base: str, timeout_seconds: float = 300):
        self.base = base.rstrip("/")
        self._timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> InternalClient:
        self._session = aiohttp.ClientSession(timeout=self._timeout)
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def post_json(self, path: str, payload: dict | None = None) -> tuple[int, Any]:
        body = _json.dumps(payload or {}, separators=(",", ":")).encode()
        return await self._send("POST", path, body, "application/json")

    async def post_form(self, path: str, fields: dict[str, str]) -> tuple[int, Any]:
        body, content_type = build_multipart(fields, file=None)
        return await self._send("POST", path, body, content_type)

    async def post_multipart(
        self,
        path: str,
        fields: dict[str, str],
        file: tuple[str, str, bytes, str],
    ) -> tuple[int, Any]:
        body, content_type = build_multipart(fields, file=file)
        return await self._send("POST", path, body, content_type)

    async def get(self, path: str) -> tuple[int, Any]:
        return await self._send("GET", path, b"", None)

    async def _send(
        self,
        method: str,
        path: str,
        body: bytes,
        content_type: str | None,
    ) -> tuple[int, Any]:
        if self._session is None:
            raise RuntimeError("InternalClient must be used as `async with`")
        headers = {"X-Internal-Auth": internal_auth.sign(method, path, body)}
        if content_type:
            headers["Content-Type"] = content_type
        async with self._session.request(
            method, f"{self.base}{path}", data=body or None, headers=headers,
        ) as resp:
            text = await resp.text()
            try:
                return resp.status, _json.loads(text) if text else None
            except _json.JSONDecodeError:
                return resp.status, text


def build_multipart(
    fields: dict[str, str],
    file: tuple[str, str, bytes, str] | None,
) -> tuple[bytes, str]:
    """Construct a multipart/form-data body. Returns (body_bytes, content_type).

    Format follows RFC 7578. Boundary is a random hex string.
    """
    boundary = "PandaSolve-" + secrets.token_hex(16)
    parts: list[bytes] = []
    for name, value in fields.items():
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
        )
        parts.append(value.encode("utf-8"))
        parts.append(b"\r\n")
    if file is not None:
        name, filename, content, mime = file
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode()
        )
        parts.append(f"Content-Type: {mime}\r\n\r\n".encode())
        parts.append(content)
        parts.append(b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)
    return body, f"multipart/form-data; boundary={boundary}"
