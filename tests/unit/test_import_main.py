"""Smoke test: the mobile-facing router graph imports + OpenAPI generates.

The legacy /tasker/api/* app instantiates Supabase eagerly at module load
(which is correct in production but unusable in unit tests). We exercise the
same router surface that bot/openapi.json is built from — and that mobile
clients actually consume — without dragging the legacy app into the import.
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")


def _build_v1_app():
    from fastapi import FastAPI

    from bot.api.v1 import router as v1_router

    app = FastAPI(title="PandaSolve API (test)", version="0.0.0")
    app.include_router(v1_router)
    return app


def test_v1_router_imports_and_mounts():
    app = _build_v1_app()
    paths = {getattr(r, "path", None) for r in app.routes}
    assert "/v1/me" in paths
    assert "/v1/tasks" in paths
    assert "/v1/devices" in paths
    assert "/v1/auth/link/start" in paths
    assert "/v1/topup/url" in paths


def test_openapi_schema_generates():
    """If a Pydantic model is malformed, openapi.json generation throws."""
    app = _build_v1_app()
    schema = app.openapi()
    assert schema["openapi"].startswith("3.")
    assert "/v1/tasks" in schema["paths"]
    assert "/v1/me" in schema["paths"]
    # ErrorResponse and the core domain types must be in the components.
    schemas = schema.get("components", {}).get("schemas", {})
    assert "MeResponse" in schemas
    assert "TaskDetail" in schemas


def test_internal_router_imports():
    """The /internal/* graph must compile too — its Depends() factories use
    bot.app.deps factories which import everything."""
    from bot.api.internal import router as internal_router  # noqa: F401
