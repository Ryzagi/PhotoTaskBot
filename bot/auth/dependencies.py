"""FastAPI dependencies that wire auth + DB lookup into route handlers."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status

from bot.app.deps import get_user_service
from bot.auth import internal as internal_auth
from bot.auth import jwt as jwt_auth
from bot.schemas.user import User
from bot.services.user_service import UserService


async def current_user(
    request: Request,
    user_service: UserService = Depends(get_user_service),
) -> User:
    """Resolve the calling user from a Supabase JWT.

    - 401 if missing/malformed/expired.
    - Creates a domain user on first sign-in (lazy provisioning).
    """
    auth_header = request.headers.get("authorization", "")
    if not auth_header.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    token = auth_header.split(" ", 1)[1].strip()
    try:
        payload = jwt_auth.verify(token)
    except jwt_auth.JWTExpired as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="token expired") from e
    except jwt_auth.JWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e

    user = await user_service.get_or_create_by_auth(payload)
    return user


async def verify_internal(request: Request) -> None:
    """Guard /internal/* routes with the bot's HMAC header."""
    header = request.headers.get("x-internal-auth", "")
    if not header:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="missing internal auth")
    body = await request.body()
    try:
        internal_auth.verify(header, request.method, request.url.path, body)
    except internal_auth.InternalAuthError as e:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(e)) from e
