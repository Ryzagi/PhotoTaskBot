"""Shared pytest fixtures and env stubs.

We never load the real .env in unit tests — secrets are stubbed here.
"""

from __future__ import annotations

import os

# Set required env vars before any bot.* module is imported. The auth modules
# read these at module level only via getenv (no module-level imports of values),
# so this stays safe.
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret-do-not-use-in-prod")
os.environ.setdefault("INTERNAL_AUTH_SECRET", "test-internal-secret-do-not-use-in-prod")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
# Supabase SDK validates the key looks like a JWT; this is a syntactically-valid
# stub (header.payload.sig) that never authenticates against any real project.
os.environ.setdefault(
    "SUPABASE_KEY",
    "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJzdHViIn0.stub",
)
os.environ.setdefault("USER_EMAIL", "test@example.com")
os.environ.setdefault("USER_PASSWORD", "test-password")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("GOOGLE_API_KEY", "test-google-key")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
