"""Google Play consumable purchase verification + credit grant.

Flow: the Android app buys a consumable via Play Billing, then POSTs the
purchaseToken to /v1/billing/google/verify. We verify the token with the Google
Play Developer API (service account), grant credits idempotently (one grant per
token, enforced by the play_purchases ledger), and reuse BillingService to add
to the user's subscription bucket.
"""

from __future__ import annotations

import httpx
import structlog
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import service_account

from bot.services.billing_service import BillingService
from bot.supabase_service import SupabaseService

log = structlog.get_logger(__name__)

_SCOPE = "https://www.googleapis.com/auth/androidpublisher"

# Play product id → solutions granted. Edit here to add or retune packs;
# prices live in the Play Console, not in code.
PRODUCT_CREDITS: dict[str, int] = {
    "bamboo_20": 20,
    "bamboo_50": 50,
    "bamboo_100": 100,
}


class PlayBillingError(Exception):
    """Verification failed or product unknown — surfaced to the client as 400."""


class PlayBillingService:
    def __init__(self, db: SupabaseService, billing: BillingService, package_name: str, sa_info: dict | None):
        self.db = db
        self.billing = billing
        self.package_name = package_name
        self._sa_info = sa_info
        self._creds = None

    @property
    def configured(self) -> bool:
        return bool(self.package_name and self._sa_info)

    def _access_token(self) -> str:
        if not self.configured:
            raise PlayBillingError("play billing not configured on the server")
        if self._creds is None:
            self._creds = service_account.Credentials.from_service_account_info(
                self._sa_info, scopes=[_SCOPE],
            )
        if not self._creds.valid:
            self._creds.refresh(GoogleAuthRequest())
        return self._creds.token

    async def verify_and_grant(self, user_id: str, product_id: str, purchase_token: str) -> dict:
        credits = PRODUCT_CREDITS.get(product_id)
        if credits is None:
            raise PlayBillingError(f"unknown product: {product_id}")

        url = (
            "https://androidpublisher.googleapis.com/androidpublisher/v3/applications/"
            f"{self.package_name}/purchases/products/{product_id}/tokens/{purchase_token}"
        )
        token = self._access_token()
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        if resp.status_code != 200:
            raise PlayBillingError(f"verification failed ({resp.status_code}): {resp.text[:200]}")
        data = resp.json()
        # purchaseState: 0 = purchased, 1 = canceled, 2 = pending
        if int(data.get("purchaseState", 1)) != 0:
            raise PlayBillingError("purchase is not in the PURCHASED state")

        # Idempotency: record the token; if it was already recorded, don't re-grant.
        first_time = await self.db.record_play_purchase(purchase_token, user_id, product_id, credits)
        if not first_time:
            bal = await self.db.get_or_reset_balance(user_id)
            log.info("play.duplicate", user_id=user_id, product_id=product_id)
            return {"granted": 0, "subscription_limit": bal["subscription_limit"]}

        new_limit = await self.billing.add_subscription(user_id, amount=credits)
        log.info("play.granted", user_id=user_id, product_id=product_id, credits=credits)
        return {"granted": credits, "subscription_limit": new_limit}
