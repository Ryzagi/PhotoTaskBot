"""Tests for bot.auth.internal — HMAC signing for bot↔backend channel."""

from __future__ import annotations

import os
import time

import pytest

from bot.auth import internal as internal_auth


def test_sign_then_verify_succeeds():
    body = b'{"hello":"world"}'
    header = internal_auth.sign("POST", "/internal/tasks/solve_image", body)
    internal_auth.verify(header, "POST", "/internal/tasks/solve_image", body)


def test_verify_with_wrong_body_fails():
    body = b'{"hello":"world"}'
    header = internal_auth.sign("POST", "/internal/tasks/solve_image", body)
    with pytest.raises(internal_auth.InternalAuthError):
        internal_auth.verify(header, "POST", "/internal/tasks/solve_image", b'{"hello":"changed"}')


def test_verify_with_wrong_path_fails():
    body = b''
    header = internal_auth.sign("GET", "/internal/users", body)
    with pytest.raises(internal_auth.InternalAuthError):
        internal_auth.verify(header, "GET", "/internal/somewhere_else", body)


def test_verify_with_wrong_method_fails():
    body = b''
    header = internal_auth.sign("POST", "/internal/users", body)
    with pytest.raises(internal_auth.InternalAuthError):
        internal_auth.verify(header, "GET", "/internal/users", body)


def test_verify_with_old_timestamp_fails():
    body = b''
    old_ts = int(time.time()) - internal_auth.DRIFT_SECONDS - 10
    import hashlib
    import hmac
    secret = os.environ["INTERNAL_AUTH_SECRET"].encode()
    body_hash = hashlib.sha256(body).hexdigest()
    payload = f"{old_ts}.GET./internal/users.{body_hash}".encode()
    sig = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    header = f"t={old_ts};sig={sig}"
    with pytest.raises(internal_auth.InternalAuthError, match="drift"):
        internal_auth.verify(header, "GET", "/internal/users", body)


def test_verify_with_wrong_secret_fails(monkeypatch):
    body = b''
    header = internal_auth.sign("GET", "/internal/users", body,
                                secret=b"some-other-secret")
    with pytest.raises(internal_auth.InternalAuthError, match="signature"):
        internal_auth.verify(header, "GET", "/internal/users", body)


def test_rotation_accepts_next_secret(monkeypatch):
    monkeypatch.setenv("INTERNAL_AUTH_SECRET_NEXT", "new-secret-during-rotation")
    body = b''
    header = internal_auth.sign(
        "GET", "/internal/users", body,
        secret=b"new-secret-during-rotation",
    )
    internal_auth.verify(header, "GET", "/internal/users", body)


def test_malformed_header_fails():
    with pytest.raises(internal_auth.InternalAuthError):
        internal_auth.verify("garbage", "GET", "/internal/users", b'')
