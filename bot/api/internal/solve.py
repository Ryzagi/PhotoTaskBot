"""Synchronous solve and image-upload endpoints, used by the Telegram bot.

The bot path stays sync for backward compatibility. Same business logic
(reserve → solve → record), just without arq enqueueing. Internal callers
get the full solution back in the response, exactly like the legacy
/tasker/api/solve_task envelope expected.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile

from bot.app.deps import get_billing, get_db, get_gemini, get_gpt
from bot.constants import SUB_FOLDER
from bot.gemini_service import GeminiSolver
from bot.gpt_service import TaskSolverGPT
from bot.services.billing_service import BillingService, OutOfQuota
from bot.supabase_service import SupabaseService

router = APIRouter()


@router.post("/upload")
async def upload_image(
    file: Annotated[bytes, File(description="A file read as bytes")],
    image_path: str = Form(...),
    telegram_user_id: int = Form(...),
    db: SupabaseService = Depends(get_db),
) -> dict:
    """Quota-gated image upload (replaces /tasker/api/download_image).

    Returns the legacy {message, status_code} envelope so the bot's existing
    handlers don't need to change their parsing.
    """
    user = await db.find_user_by_telegram_id(telegram_user_id)
    if not user:
        return {"message": "User not found", "status_code": 404}
    try:
        await db.upload_image(f"{SUB_FOLDER.lstrip('/')}{image_path}", file)
        return {"message": "File uploaded successfully", "status_code": 200}
    except Exception as e:
        return {"message": "upload failed", "status_code": 500, "error": str(e)}


@router.post("/tasks/get_existing")
async def get_existing_solution(
    image_path: str = Form(...),
    telegram_user_id: int = Form(...),
    db: SupabaseService = Depends(get_db),
) -> dict:
    """Look up a cached solution for a previously-solved image."""
    user = await db.find_user_by_telegram_id(telegram_user_id)
    if not user:
        return {"message": [], "status_code": 404}
    resp = (
        db.supabase_client.table(db._task_table)
        .select("solution")
        .eq("user_uuid", str(user.id))
        .eq("image_path", image_path)
        .execute()
    )
    return {"message": resp.data or [], "status_code": 200}


@router.post("/tasks/latex_to_text")
async def latex_to_text(
    text: str = Form(...),
    telegram_user_id: int = Form(...),
    db: SupabaseService = Depends(get_db),
    gemini: GeminiSolver = Depends(get_gemini),
) -> dict:
    """Convert a LaTeX solution to plain Unicode via Gemini."""
    user = await db.find_user_by_telegram_id(telegram_user_id)
    if not user:
        return {"message": "User not found", "status_code": 404}
    try:
        answer = await gemini.generate_unicode_solution(text)
        await db.insert_legacy_solution(
            user_id=user.id, file_path="", solution=answer, model="gemini-2.5-flash",
        )
        return {"message": "Task solved", "answer": answer}
    except Exception as e:
        return {"message": "latex_to_text failed", "status_code": 500, "error": str(e)}


@router.post("/tasks/solve_image")
async def solve_image(
    file: UploadFile = File(...),
    telegram_user_id: int = Form(...),
    caption: str | None = Form(default=None),
    db: SupabaseService = Depends(get_db),
    billing: BillingService = Depends(get_billing),
    gpt: TaskSolverGPT = Depends(get_gpt),
    gemini: GeminiSolver = Depends(get_gemini),
) -> dict:
    user = await db.find_user_by_telegram_id(telegram_user_id)
    if not user:
        return {"error": "user_not_found"}
    try:
        reservation = await billing.reserve(user.id)
    except OutOfQuota:
        return {"error": "daily_limit_reached", "status_code": 429}

    try:
        answer = await gpt.solve(file, caption=caption)
        model = "gpt-5-mini"
    except Exception:
        await file.seek(0)
        try:
            answer = await gemini.solve(file, caption=caption)
            model = "gemini-2.5-flash"
        except Exception as e:
            await billing.refund(user.id, reservation.spent_from)
            return {"error": "solver_failed", "detail": str(e)}

    await db.insert_legacy_solution(user_id=user.id, file_path="", solution=answer, model=model)
    return {"message": "Task solved", "answer": answer}


@router.post("/tasks/solve_text")
async def solve_text(
    text: str = Form(...),
    telegram_user_id: int = Form(...),
    db: SupabaseService = Depends(get_db),
    billing: BillingService = Depends(get_billing),
    gpt: TaskSolverGPT = Depends(get_gpt),
    gemini: GeminiSolver = Depends(get_gemini),
) -> dict:
    user = await db.find_user_by_telegram_id(telegram_user_id)
    if not user:
        return {"error": "user_not_found"}
    try:
        reservation = await billing.reserve(user.id)
    except OutOfQuota:
        return {"error": "daily_limit_reached", "status_code": 429}

    try:
        answer = await gpt.generate_text_solution(text)
    except Exception:
        try:
            answer = await gemini.generate_text(text)
        except Exception as e:
            await billing.refund(user.id, reservation.spent_from)
            return {"error": "solver_failed", "detail": str(e)}

    await db.insert_legacy_solution(user_id=user.id, file_path="", solution=answer, model="gemini-2.5-flash")
    return {"message": "Task solved", "answer": answer}
