"""Authentication primitives.

- `jwt.verify` validates Supabase HS256 JWTs locally (no round-trip to /auth/v1/user).
- `internal.verify` validates HMAC-signed X-Internal-Auth headers from the bot.
- `dependencies.current_user` is the FastAPI dependency injected into /v1/* routes.
"""
