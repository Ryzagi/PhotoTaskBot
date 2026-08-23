"""Identity endpoints: /v1/me, /v1/me/balance."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from bot.app.deps import get_user_service
from bot.auth.dependencies import current_user
from bot.schemas.user import MeResponse, UpdateMeRequest
from bot.services.user_service import UserService

router = APIRouter(tags=["identity"])


@router.get("/me", response_model=MeResponse)
async def get_me(
    user=Depends(current_user),
    user_service: UserService = Depends(get_user_service),
) -> MeResponse:
    balance = await user_service.get_balance(user.id)
    stats = await user_service.get_stats(user.id)
    return MeResponse(
        id=user.id,
        telegram_linked=user.telegram_linked,
        language_code=user.language_code,
        display_name=user.display_name,
        balance=balance,
        created_at=user.created_at,
        solved_count=stats["solved_count"],
        streak=stats["streak"],
    )


@router.post("/me", response_model=MeResponse)
async def update_me(
    payload: UpdateMeRequest,
    user=Depends(current_user),
    user_service: UserService = Depends(get_user_service),
) -> MeResponse:
    if payload.language_code:
        user = await user_service.update_language(user.id, payload.language_code)
    if payload.display_name is not None:
        user = await user_service.update_display_name(user.id, payload.display_name)
    balance = await user_service.get_balance(user.id)
    stats = await user_service.get_stats(user.id)
    return MeResponse(
        id=user.id,
        telegram_linked=user.telegram_linked,
        language_code=user.language_code,
        display_name=user.display_name,
        balance=balance,
        created_at=user.created_at,
        solved_count=stats["solved_count"],
        streak=stats["streak"],
    )
