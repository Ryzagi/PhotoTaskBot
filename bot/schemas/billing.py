from __future__ import annotations

from pydantic import BaseModel, Field


class PlayVerifyRequest(BaseModel):
    """Sent by the Android app after a successful Play Billing purchase."""

    product_id: str = Field(min_length=1, max_length=100)
    purchase_token: str = Field(min_length=1, max_length=4000)


class PlayVerifyResponse(BaseModel):
    granted: int            # credits added this call (0 if the token was already processed)
    subscription_limit: int  # the user's new subscription bucket
