"""Quota reservation and refund — Python-side, keyed on user_id text."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from bot.supabase_service import SupabaseService

Bucket = Literal["daily", "subscription"]


class OutOfQuota(Exception):
    """Raised when neither daily nor subscription limit can be debited."""


@dataclass
class Reservation:
    spent_from: Bucket
    remaining: int


class BillingService:
    def __init__(self, db: SupabaseService):
        self.db = db

    async def reserve(self, user_id: str) -> Reservation:
        row = await self.db.rpc_reserve_solve(user_id)
        if row["spent_from"] is None or row["remaining"] < 0:
            raise OutOfQuota()
        return Reservation(spent_from=row["spent_from"], remaining=row["remaining"])

    async def refund(self, user_id: str, bucket: Bucket) -> None:
        await self.db.rpc_refund_solve(user_id, bucket)

    async def add_subscription(self, user_id: str, amount: int = 1):
        return await self.db.add_subscription_limit(user_id, amount)
