"""Verify that InternalClient signs requests the way the backend expects.

We don't make real network calls — we hand-roll the signature with the same
inputs InternalClient would, and verify it.
"""

from __future__ import annotations

from bot.auth import internal as internal_auth


def test_signed_get_round_trip():
    header = internal_auth.sign("GET", "/internal/users", b"")
    internal_auth.verify(header, "GET", "/internal/users", b"")


def test_signed_post_round_trip():
    body = b'{"telegram_user_id": 12345}'
    header = internal_auth.sign("POST", "/internal/topup", body)
    internal_auth.verify(header, "POST", "/internal/topup", body)


def test_signature_includes_body():
    body = b'{"a":1}'
    header = internal_auth.sign("POST", "/internal/x", body)
    # Same path/method/header but a different body should fail.
    import pytest
    with pytest.raises(internal_auth.InternalAuthError):
        internal_auth.verify(header, "POST", "/internal/x", b'{"a":2}')
