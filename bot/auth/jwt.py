"""Supabase JWT verification.

We do HS256 local verification with SUPABASE_JWT_SECRET. Do not call
/auth/v1/user per request — Supabase's docs explicitly recommend local verify
for performance, and round-tripping doubles request latency.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime

import jwt as pyjwt


class JWTError(Exception):
    pass


class JWTExpired(JWTError):
    pass


@dataclass
class JWTPayload:
    sub: str           # Supabase auth user UUID
    email: str | None
    role: str          # "authenticated"
    exp: int

    @classmethod
    def from_dict(cls, d: dict) -> JWTPayload:
        return cls(
            sub=d["sub"],
            email=d.get("email"),
            role=d.get("role", "authenticated"),
            exp=int(d.get("exp", 0)),
        )


def verify(token: str) -> JWTPayload:
    secret = os.environ.get("SUPABASE_JWT_SECRET")
    if not secret:
        raise JWTError("SUPABASE_JWT_SECRET not configured")
    try:
        decoded = pyjwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except pyjwt.ExpiredSignatureError as e:
        raise JWTExpired(str(e)) from e
    except pyjwt.InvalidTokenError as e:
        raise JWTError(str(e)) from e

    if decoded.get("exp", 0) < datetime.now(UTC).timestamp():
        raise JWTExpired("token expired")
    return JWTPayload.from_dict(decoded)
