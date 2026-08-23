from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class Balance(BaseModel):
    daily: int = Field(ge=0)
    subscription: int = Field(ge=0)


class User(BaseModel):
    # The domain key is `user_id text` — Telegram id for bot users, the Supabase
    # auth UUID (as text) for mobile users.
    id: str
    telegram_user_id: int | None = None
    auth_user_id: str | None = None
    language_code: str = "ru"
    display_name: str | None = None
    is_premium: bool = False
    created_at: datetime

    @property
    def telegram_linked(self) -> bool:
        return self.telegram_user_id is not None


class MeResponse(BaseModel):
    id: str
    telegram_linked: bool
    language_code: str
    display_name: str | None = None
    balance: Balance
    created_at: datetime
    solved_count: int = 0           # total tasks solved (status=done)
    streak: int = 0                 # consecutive days (ending today/yesterday) with a solve


class UpdateMeRequest(BaseModel):
    language_code: str | None = None
    display_name: str | None = Field(default=None, max_length=60)


class LinkStartResponse(BaseModel):
    code: str
    expires_at: datetime


class LinkConfirmRequest(BaseModel):
    code: str
    telegram_user_id: int
