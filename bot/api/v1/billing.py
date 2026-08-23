"""Google Play billing verification (consumable top-ups)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from bot.app.deps import get_play_billing
from bot.auth.dependencies import current_user
from bot.schemas.billing import PlayVerifyRequest, PlayVerifyResponse
from bot.services.play_billing import PlayBillingError, PlayBillingService

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/google/verify", response_model=PlayVerifyResponse)
async def verify_google_purchase(
    payload: PlayVerifyRequest,
    user=Depends(current_user),
    play: PlayBillingService = Depends(get_play_billing),
) -> PlayVerifyResponse:
    """Verify a Play purchase token server-side and grant credits (idempotent)."""
    try:
        result = await play.verify_and_grant(user.id, payload.product_id, payload.purchase_token)
    except PlayBillingError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return PlayVerifyResponse(
        granted=result["granted"],
        subscription_limit=result["subscription_limit"],
    )
