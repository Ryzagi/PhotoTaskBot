"""Bot-side user upsert (called from /start), balance, list, and admin ops."""

from __future__ import annotations

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
    """Admin: every Telegram-reachable user id, for broadcasts.

    In the text-key model the Telegram id is stored in `user_id` (digits);
    mobile users have a UUID there, so we keep only the numeric ones."""
    db._ensure_session()
    resp = (
        db.supabase_client.table(db._users_table)
        .select("user_id")
        .execute()
    )
    return {
        "message": [
            {"user_id": int(row["user_id"])}
            for row in (resp.data or [])
            if str(row.get("user_id") or "").isdigit()
        ],
        "status_code": 200,
    }


@router.post("/admin/add_subscription_for_all")
async def add_subscription_for_all(
    data: dict,
    db: SupabaseService = Depends(get_db),
    billing: BillingService = Depends(get_billing),
) -> dict:
    """Admin: bulk-add subscription credits. Returns Telegram ids so the bot
    can DM each. Telegram users are the rows whose `user_id` is numeric."""
    amount = int(data["limit"])
    db._ensure_session()
    resp = (
        db.supabase_client.table(db._users_table)
        .select("user_id")
        .execute()
    )
    out: list[dict] = []
    for row in (resp.data or []):
        uid = str(row.get("user_id") or "")
        if not uid.isdigit():
            continue
        await billing.add_subscription(uid, amount=amount)
        out.append({"user_id": int(uid)})
    return {"message": out, "status_code": 200}
