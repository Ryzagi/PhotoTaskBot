"""Bot-side user upsert (called from /start), balance, list, and admin ops."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Form

from bot.app.deps import get_billing, get_db
from bot.services.billing_service import BillingService
from bot.supabase_service import SupabaseService

router = APIRouter()


@router.post("/users")
async def upsert_telegram_user(
    data: dict,
    db: SupabaseService = Depends(get_db),
) -> dict:
    """Bot's /start handler calls this. data = full Telegram user object."""
    await db.upsert_telegram_user(data)
    return {"ok": True}


@router.post("/topup")
async def topup_subscription(
    data: dict,
    db: SupabaseService = Depends(get_db),
    billing: BillingService = Depends(get_billing),
) -> dict:
    """Bot calls this after a successful Telegram Stars payment."""
    user = await db.find_user_by_telegram_id(int(data["telegram_user_id"]))
    if not user:
        return {"error": "user_not_found"}
    new_limit = await billing.add_subscription(user.id, amount=int(data.get("amount", 1)))
    return {"subscription_limit": new_limit}


@router.post("/balance")
async def get_balance(
    telegram_user_id: int = Form(...),
    db: SupabaseService = Depends(get_db),
) -> dict:
    """Returns the legacy bot envelope so callers can swap in without
    relearning the shape."""
    user = await db.find_user_by_telegram_id(telegram_user_id)
    if not user:
        return {"message": "User not found", "status_code": 404}
    bal = await db.get_or_reset_balance(user.id)
    return {
        "message": [{
            "daily_limit": bal["daily_limit"],
            "subscription_limit": bal["subscription_limit"],
        }],
        "status_code": 200,
    }


@router.post("/users/list")
async def list_users(db: SupabaseService = Depends(get_db)) -> dict:
    """Admin: returns every telegram-linked user ID for broadcasts."""
    resp = (
        db.supabase_client.table(db._users_table)
        .select("telegram_user_id")
        .neq("telegram_user_id", None)
        .execute()
    )
    return {
        "message": [
            {"user_id": row["telegram_user_id"]}
            for row in (resp.data or [])
            if row.get("telegram_user_id") is not None
        ],
        "status_code": 200,
    }


@router.post("/admin/add_subscription_for_all")
async def add_subscription_for_all(
    data: dict,
    db: SupabaseService = Depends(get_db),
    billing: BillingService = Depends(get_billing),
) -> dict:
    """Admin: bulk-add subscription credits. Returns telegram_user_ids so the
    bot can DM each."""
    amount = int(data["limit"])
    resp = (
        db.supabase_client.table(db._users_table)
        .select("id, telegram_user_id")
        .neq("telegram_user_id", None)
        .execute()
    )
    rows = resp.data or []
    out: list[dict] = []
    for row in rows:
        if not row.get("telegram_user_id"):
            continue
        await billing.add_subscription(UUID(row["id"]), amount=amount)
        out.append({"user_id": row["telegram_user_id"]})
    return {"message": out, "status_code": 200}
