"""Smoke test for the shared error envelope helper."""

from __future__ import annotations

from bot.schemas.errors import ErrorResponse, make


def test_make_error_minimal():
    body = make("rate_limited", "Slow down.")
    assert body == {"error": {"code": "rate_limited", "message": "Slow down.", "details": None}}
    parsed = ErrorResponse.model_validate(body)
    assert parsed.error.code == "rate_limited"


def test_make_error_with_details():
    body = make("daily_limit_reached", "Out.", {"retry_after_seconds": 86400})
    assert body["error"]["details"] == {"retry_after_seconds": 86400}
    ErrorResponse.model_validate(body)  # raises on schema mismatch
