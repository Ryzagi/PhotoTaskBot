"""Bot calls this after the user pastes a 6-digit code in chat."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from bot.app.deps import get_user_service
from bot.schemas.user import LinkConfirmRequest
from bot.services.user_service import UserService

router = APIRouter()


@router.post("/auth/link/confirm")
async def link_confirm(
    payload: LinkConfirmRequest,
    user_service: UserService = Depends(get_user_service),
) -> dict:
    try:
        merged_user_id = await user_service.confirm_link(
            payload.code, payload.telegram_user_id
        )
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return {"user_id": str(merged_user_id)}
