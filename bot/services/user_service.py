"""Domain user lookup + provisioning + Telegram linking. Keyed on user_id text."""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from bot.auth.jwt import JWTPayload
from bot.schemas.user import Balance, LinkStartResponse, User
from bot.supabase_service import SupabaseService

LINK_CODE_TTL = timedelta(minutes=5)


class UserService:
    def __init__(self, db: SupabaseService):
        self.db = db

    async def get_or_create_by_auth(self, payload: JWTPayload) -> User:
        existing = await self.db.find_user_by_auth_id(payload.sub)
        if existing:
            return existing
        return await self.db.create_user_from_auth(auth_user_id=payload.sub, email=payload.email)

    async def get_balance(self, user_id: str) -> Balance:
        row = await self.db.get_or_reset_balance(user_id)
        return Balance(daily=row["daily_limit"], subscription=row["subscription_limit"])

    async def issue_link_code(self, user_id: str) -> LinkStartResponse:
        code = f"{secrets.randbelow(1_000_000):06d}"
        code_hash = hashlib.sha256(code.encode()).digest()
        expires_at = datetime.now(UTC) + LINK_CODE_TTL
        await self.db.insert_link_code(code_hash, user_id, expires_at)
        return LinkStartResponse(code=code, expires_at=expires_at)

    async def confirm_link(self, code: str, telegram_user_id: int) -> str:
        """Bot calls this via /internal/auth/link/confirm. Merges the mobile
        user row into the Telegram-id row when both exist."""
        code_hash = hashlib.sha256(code.encode()).digest()
        link_row = await self.db.consume_link_code(code_hash)
        if not link_row:
            raise ValueError("invalid or expired code")
        mobile_user_id: str = link_row["user_id"]

        existing_telegram_user = await self.db.find_user_by_telegram_id(telegram_user_id)
        if existing_telegram_user is None:
            await self.db.set_telegram_user_id(mobile_user_id, telegram_user_id)
            return mobile_user_id

        await self.db.merge_users(survivor=existing_telegram_user.id, victim=mobile_user_id)
        return existing_telegram_user.id

    async def update_language(self, user_id: str, language_code: str) -> User:
        return await self.db.update_user_language(user_id, language_code)
