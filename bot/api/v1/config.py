"""Public config endpoints (no auth)."""

from __future__ import annotations

from fastapi import APIRouter

from bot.constants import DEFAULT_DAILY_LIMIT

router = APIRouter(tags=["config"])


@router.get("/config")
async def get_config() -> dict:
    return {
        "daily_limit": DEFAULT_DAILY_LIMIT,
        "max_image_bytes": 10 * 1024 * 1024,
        "supported_locales": ["ru", "en"],
        "telegram_bot_username": "PandaSolveBot",
    }


@router.get("/topup/url")
async def topup_url() -> dict:
    return {"url": "https://t.me/PandaSolveBot?start=topup"}
