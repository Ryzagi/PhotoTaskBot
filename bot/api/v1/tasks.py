"""Async task creation, polling, and history."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import JSONResponse

from bot.app.deps import get_task_service
from bot.auth.dependencies import current_user
from bot.schemas.errors import make as err
from bot.schemas.task import (
    ChatRequest,
    ChatThread,
    TaskCreateText,
    TaskDetail,
    TaskList,
    TaskRef,
    TaskUpdate,
)
from bot.services.billing_service import OutOfQuota
from bot.services.task_service import TaskService

router = APIRouter(tags=["tasks"])


@router.post("/tasks", response_model=TaskRef, status_code=status.HTTP_202_ACCEPTED)
async def create_image_task(
    file: UploadFile = File(...),
    caption: str | None = Form(default=None),
    user=Depends(current_user),
    tasks_service: TaskService = Depends(get_task_service),
):
    raw = await file.read()
    if len(raw) > 10 * 1024 * 1024:
        return JSONResponse(
            err("image_too_large", "Image exceeds 10MB."),
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )
    try:
        task_id = await tasks_service.create_image_task(user.id, raw, caption)
    except OutOfQuota:
        return JSONResponse(
            err(
                "daily_limit_reached",
                "Daily limit reached. Try again tomorrow or top up via Telegram.",
                {"retry_after_seconds": 86400},
            ),
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )
    return TaskRef(task_id=task_id, status="pending")


@router.post("/tasks/text", response_model=TaskRef, status_code=status.HTTP_202_ACCEPTED)
async def create_text_task(
    payload: TaskCreateText,
    user=Depends(current_user),
    tasks_service: TaskService = Depends(get_task_service),
):
    try:
        task_id = await tasks_service.create_text_task(user.id, payload.text)
    except OutOfQuota:
        return JSONResponse(
            err(
                "daily_limit_reached",
                "Daily limit reached. Try again tomorrow or top up via Telegram.",
                {"retry_after_seconds": 86400},
            ),
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )
    return TaskRef(task_id=task_id, status="pending")


@router.get("/tasks/{task_id}", response_model=TaskDetail)
async def get_task(
    task_id: str,
    user=Depends(current_user),
    tasks_service: TaskService = Depends(get_task_service),
):
    task = await tasks_service.get(user.id, task_id)
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="task not found")
    return task


@router.get("/tasks", response_model=TaskList)
async def list_tasks(
    limit: int = Query(default=20, ge=1, le=50),
    before: datetime | None = Query(default=None),
    album_id: UUID | None = Query(default=None),
    q: str | None = Query(default=None, max_length=200),
    user=Depends(current_user),
    tasks_service: TaskService = Depends(get_task_service),
):
    return await tasks_service.list(user.id, limit=limit, before=before, album_id=album_id, q=q)


@router.patch("/tasks/{task_id}", response_model=TaskDetail)
async def rename_task(
    task_id: str,
    payload: TaskUpdate,
    user=Depends(current_user),
    tasks_service: TaskService = Depends(get_task_service),
) -> TaskDetail:
    task = await tasks_service.rename(user.id, task_id, payload.title)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="task not found")
    return task


@router.get("/tasks/{task_id}/chat", response_model=ChatThread)
async def get_chat(
    task_id: str,
    user=Depends(current_user),
    tasks_service: TaskService = Depends(get_task_service),
) -> ChatThread:
    result = await tasks_service.chat_history(user.id, task_id)
    if result is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="task not found")
    msgs, remaining = result
    return ChatThread(messages=msgs, remaining=remaining)


@router.post("/tasks/{task_id}/chat", response_model=ChatThread)
async def post_chat(
    task_id: str,
    payload: ChatRequest,
    user=Depends(current_user),
    tasks_service: TaskService = Depends(get_task_service),
) -> ChatThread:
    result = await tasks_service.chat(user.id, task_id, payload.message)
    if result is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="task not found")
    msgs, remaining = result
    return ChatThread(messages=msgs, remaining=remaining)
