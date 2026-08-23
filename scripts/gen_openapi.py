"""Emit bot/openapi.json from the FastAPI app.

Run from the repo root: `python -m scripts.gen_openapi`.

Stubs all required env vars before importing — no real Supabase, OpenAI, etc.
needed. FastAPI's `app.openapi()` only walks route definitions; the lazy
`Depends()` factories are not invoked.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

# Stub environment so imports that read env vars at module load don't fail.
_stubs = {
    "SUPABASE_JWT_SECRET": "stub",
    "INTERNAL_AUTH_SECRET": "stub",
    "SUPABASE_URL": "https://example.supabase.co",
    "SUPABASE_KEY": "stub",
    "SUPABASE_SERVICE_ROLE_KEY": "stub",
    "USER_EMAIL": "stub@example.com",
    "USER_PASSWORD": "stub",
    "OPENAI_API_KEY": "stub",
    "GOOGLE_API_KEY": "stub",
    "TELEGRAM_BOT_TOKEN": "0:stub",
    "ADMIN_TG_ID": "0",
    "REDIS_URL": "redis://localhost:6379",
    "APNS_AUTH_KEY_BASE64": "",
    "APNS_KEY_ID": "",
    "APNS_TEAM_ID": "",
    "APNS_BUNDLE_ID": "app.pandasolve.client",
    "FCM_SERVICE_ACCOUNT_JSON_BASE64": "",
}
for k, v in _stubs.items():
    os.environ.setdefault(k, v)


def main() -> None:
    """Build a schema-only FastAPI app from the public surfaces.

    We intentionally bypass bot.app.main because its import chain pulls in the
    legacy /tasker/api/* app, which instantiates Supabase at module load —
    fine in prod, but not what we want for codegen.

    Mobile clients only consume /v1/*, so that's all we emit.
    """
    from fastapi import FastAPI

    from bot.api.v1 import router as v1_router

    app = FastAPI(
        title="PandaSolve API",
        version="0.2.0",
        description="Mobile-facing public API. Source of truth for mobile codegen.",
    )
    app.include_router(v1_router)

    schema = app.openapi()
    out = Path(__file__).resolve().parents[1] / "bot" / "openapi.json"
    out.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size} bytes, {len(schema.get('paths', {}))} paths)")


if __name__ == "__main__":
    main()
