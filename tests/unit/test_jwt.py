"""Tests for bot.auth.jwt — local HS256 Supabase JWT verification."""

from __future__ import annotations

import os
import time

import jwt as pyjwt
import pytest

from bot.auth import jwt as jwt_auth


def _make_token(payload_overrides: dict | None = None, secret: str | None = None) -> str:
    secret = secret or os.environ["SUPABASE_JWT_SECRET"]
    payload = {
        "sub": "11111111-1111-1111-1111-111111111111",
        "email": "user@example.com",
        "aud": "authenticated",
        "role": "authenticated",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
    }
    if payload_overrides:
        payload.update(payload_overrides)
    return pyjwt.encode(payload, secret, algorithm="HS256")


def test_verify_valid_token_returns_payload():
    token = _make_token()
    payload = jwt_auth.verify(token)
    assert payload.sub == "11111111-1111-1111-1111-111111111111"
    assert payload.email == "user@example.com"
    assert payload.role == "authenticated"


def test_verify_expired_token_raises():
    token = _make_token({"exp": int(time.time()) - 60})
    with pytest.raises(jwt_auth.JWTExpired):
        jwt_auth.verify(token)


def test_verify_wrong_audience_raises():
    token = _make_token({"aud": "anon"})
    with pytest.raises(jwt_auth.JWTError):
        jwt_auth.verify(token)


def test_verify_wrong_secret_raises():
    token = _make_token(secret="someone-elses-secret")
    with pytest.raises(jwt_auth.JWTError):
        jwt_auth.verify(token)


def test_verify_garbage_raises():
    with pytest.raises(jwt_auth.JWTError):
        jwt_auth.verify("not-even-a-jwt")
