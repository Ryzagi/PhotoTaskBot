"""Telegram account-linking — mobile-side endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from bot.app.deps import get_user_service
from bot.auth.dependencies import current_user
from bot.schemas.user import LinkStartResponse
from bot.services.user_service import UserService

router = APIRouter(tags=["auth"])


@router.post("/auth/link/start", response_model=LinkStartResponse)
async def link_start(
    user=Depends(current_user),
    user_service: UserService = Depends(get_user_service),
) -> LinkStartResponse:
    return await user_service.issue_link_code(user.id)
