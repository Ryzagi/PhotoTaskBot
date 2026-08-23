"""HMAC-signed internal request authentication.

The Telegram bot is the only legitimate caller of /internal/*. We sign each
request with an HMAC-SHA256 over `{timestamp}.{method}.{path}.{sha256(body)}`
keyed by INTERNAL_AUTH_SECRET. Replay protection: reject if |now - ts| > 60s.

Header shape:
    X-Internal-Auth: t=<unix_ts>;sig=<hex>
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time

DRIFT_SECONDS = 60


class InternalAuthError(Exception):
    pass


def _secrets() -> list[bytes]:
    """Return one or two secrets (for graceful rotation)."""
    primary = os.environ.get("INTERNAL_AUTH_SECRET")
    if not primary:
        raise InternalAuthError("INTERNAL_AUTH_SECRET not configured")
    out = [primary.encode()]
    nxt = os.environ.get("INTERNAL_AUTH_SECRET_NEXT")
    if nxt:
        out.append(nxt.encode())
    return out


def _parse_header(header: str) -> tuple[int, str]:
    parts = dict(p.split("=", 1) for p in header.split(";") if "=" in p)
    if "t" not in parts or "sig" not in parts:
        raise InternalAuthError("malformed X-Internal-Auth header")
    try:
        ts = int(parts["t"])
    except ValueError as e:
        raise InternalAuthError("bad timestamp") from e
    return ts, parts["sig"]


def sign(method: str, path: str, body: bytes, secret: bytes | None = None) -> str:
    """Used by the bot to sign outgoing requests."""
    secret = secret or _secrets()[0]
    ts = int(time.time())
    body_hash = hashlib.sha256(body).hexdigest()
    payload = f"{ts}.{method.upper()}.{path}.{body_hash}".encode()
    sig = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    return f"t={ts};sig={sig}"


def verify(header: str, method: str, path: str, body: bytes) -> None:
    """Raise InternalAuthError if the request is not authentic."""
    ts, sig_hex = _parse_header(header)
    drift = abs(time.time() - ts)
    if drift > DRIFT_SECONDS:
        raise InternalAuthError(f"timestamp drift too large: {drift:.0f}s")
    body_hash = hashlib.sha256(body).hexdigest()
    payload = f"{ts}.{method.upper()}.{path}.{body_hash}".encode()
    for secret in _secrets():
        expected = hmac.new(secret, payload, hashlib.sha256).hexdigest()
        if hmac.compare_digest(expected, sig_hex):
            return
    raise InternalAuthError("signature mismatch")
