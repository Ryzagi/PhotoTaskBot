"""Standard error envelope for all /v1/* responses.

Every error follows this shape:
    { "error": { "code": "rate_limited", "message": "...", "details": {...} } }
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


def make(code: str, message: str, details: dict[str, Any] | None = None) -> dict:
    """Convenience for JSONResponse content."""
    return {"error": {"code": code, "message": message, "details": details}}
