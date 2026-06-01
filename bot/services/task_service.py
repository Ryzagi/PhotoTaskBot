"""Task creation, polling, and history. Keyed on user_id text; task ids are the
DB-assigned bigint, surfaced as strings."""

from __future__ import annotations

import io
import uuid
from datetime import UTC, datetime
from typing import Literal

from PIL import Image, ImageOps

from bot.schemas.task import Solution, TaskDetail, TaskList, TaskListItem
from bot.services.billing_service import BillingService
from bot.supabase_service import SupabaseService

InputKind = Literal["image", "text", "latex"]

FREE_CHAT_LIMIT = 3   # free follow-up questions per task before a top-up is needed


def _remaining(messages: list[dict]) -> int:
    used = sum(1 for m in messages if m.get("role") == "user")
    return max(0, FREE_CHAT_LIMIT - used)


class TaskService:
    THUMB_SIZE = (256, 256)
    JPEG_QUALITY = 80

    def __init__(self, db: SupabaseService, billing: BillingService, queue, gpt=None, gemini=None):
        self.db = db
        self.billing = billing
        self.queue = queue  # arq pool, or None → solve inline in-request
        self.gpt = gpt
        self.gemini = gemini

    async def create_image_task(self, user_id: str, file_bytes: bytes, caption: str | None) -> str:
        reservation = await self.billing.reserve(user_id)
        stamp = uuid.uuid4().hex
        image_path = f"task_images/{user_id}/{datetime.now(UTC):%Y/%m}/{stamp}.jpg"

        img = Image.open(io.BytesIO(file_bytes))
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=85, optimize=True)
        jpeg = buf.getvalue()
        await self.db.upload_image(image_path, jpeg)

        img.thumbnail(self.THUMB_SIZE)
        thumb_buf = io.BytesIO()
        img.save(thumb_buf, "JPEG", quality=self.JPEG_QUALITY, optimize=True)
        thumbnail_path = image_path.replace("task_images/", "task_thumbs/")
        await self.db.upload_image(thumbnail_path, thumb_buf.getvalue())

        task_id = await self.db.insert_task(
            user_id=user_id,
            status="pending",
            input_kind="image",
            input_text=caption,
            image_path=image_path,
            thumbnail_path=thumbnail_path,
        )
        if self.queue is not None:
            await self.queue.enqueue_job("solve_image_task", task_id)
        else:
            await self._solve_inline(task_id, user_id, reservation.spent_from, image_bytes=jpeg, caption=caption)
        return task_id

    async def create_text_task(self, user_id: str, text: str) -> str:
        reservation = await self.billing.reserve(user_id)
        task_id = await self.db.insert_task(
            user_id=user_id,
            status="pending",
            input_kind="text",
            input_text=text,
            image_path=None,
            thumbnail_path=None,
        )
        if self.queue is not None:
            await self.queue.enqueue_job("solve_text_task", task_id)
        else:
            await self._solve_inline(task_id, user_id, reservation.spent_from, text=text)
        return task_id

    async def _solve_inline(
        self, task_id: str, user_id: str, spent_from: str,
        image_bytes: bytes | None = None, caption: str | None = None, text: str | None = None,
    ) -> None:
        """Synchronous solve fallback used when no Redis worker is configured."""
        try:
            if image_bytes is not None:
                try:
                    answer = await self.gpt.solve(io.BytesIO(image_bytes), caption=caption)
                    model = "gpt-5-mini"
                except Exception:
                    answer = await self.gemini.solve(io.BytesIO(image_bytes), caption=caption)
                    model = "gemini-2.5-flash"
            else:
                try:
                    answer = await self.gpt.generate_text_solution(text)
                    model = "gpt-5-mini"
                except Exception:
                    answer = await self.gemini.generate_text(text)
                    model = "gemini-2.5-flash"
            await self.db.mark_task_done(task_id, solution=answer, model_used=model)
        except Exception as e:
            await self.db.mark_task_failed(task_id, error_code="solver_failed", detail=str(e))
            await self.billing.refund(user_id, spent_from)

    async def get(self, user_id: str, task_id: str) -> TaskDetail | None:
        row = await self.db.get_task(task_id)
        if row is None or row.get("user_id") != user_id:
            return None
        # NOTE: signed-URL generation is skipped — the mobile client renders math
        # natively and shows no image/thumbnail. Generating them was 2 Supabase
        # Storage round-trips per detail (and 1 per list row) of pure latency for
        # unused data. Re-add lazily (or via a `?thumbnails=true` flag) if a client
        # ever needs them.
        return TaskDetail(
            id=row["id"],
            status=row.get("status") or "done",
            input_kind=row.get("input_kind") or ("image" if row.get("file_path") else "text"),
            input_text=row.get("input_text"),
            thumbnail_url=None,
            image_url=None,
            solution=Solution.model_validate(row["solution"]) if row.get("solution") else None,
            album_id=str(row["album_id"]) if row.get("album_id") else None,
            model_used=row.get("model_used"),
            error_code=row.get("error_code"),
            created_at=row["created_at"],
            completed_at=row.get("completed_at"),
        )

    async def _owned_task(self, user_id: str, task_id: str) -> dict | None:
        row = await self.db.get_task(task_id)
        if row is None or row.get("user_id") != user_id:
            return None
        return row

    async def rename(self, user_id: str, task_id: str, title: str) -> TaskDetail | None:
        if await self._owned_task(user_id, task_id) is None:
            return None
        await self.db.update_task_title(user_id, task_id, title.strip())
        return await self.get(user_id, task_id)

    async def chat_history(self, user_id: str, task_id: str) -> tuple[list[dict], int] | None:
        if await self._owned_task(user_id, task_id) is None:
            return None
        msgs = await self.db.list_messages(task_id)
        return msgs, _remaining(msgs)

    async def chat(self, user_id: str, task_id: str, message: str) -> tuple[list[dict], int] | None:
        """Follow-up Q&A: store the question, answer it with the task as context, store the reply.
        Capped at FREE_CHAT_LIMIT questions per task; beyond that the client prompts a top-up."""
        task = await self._owned_task(user_id, task_id)
        if task is None:
            return None

        history = await self.db.list_messages(task_id)
        if _remaining(history) <= 0:
            return history, 0   # limit reached — don't spend an LLM call

        solution = task.get("solution") or {}
        sols = solution.get("solutions") or []
        problem = sols[0].get("problem", "") if sols else (task.get("input_text") or "")
        parts: list[str] = []
        for p in sols:
            for blk in (p.get("steps") or []):
                parts.append(blk.get("content", ""))
            for blk in (p.get("solution") or []):
                parts.append(blk.get("content", ""))
        solution_text = "\n".join(parts)

        await self.db.insert_message(task_id, user_id, "user", message)
        try:
            reply = await self.gpt.generate_chat_reply(
                problem, solution_text,
                [{"role": m["role"], "content": m["content"]} for m in history],
                message,
            )
        except Exception:
            reply = "Не удалось ответить — попробуй переформулировать вопрос чуть позже 🐼"
        await self.db.insert_message(task_id, user_id, "assistant", reply)
        msgs = await self.db.list_messages(task_id)
        return msgs, _remaining(msgs)

    async def list(self, user_id: str, limit: int, before: datetime | None, album_id: str | None = None, q: str | None = None) -> TaskList:
        rows = await self.db.list_tasks(user_id, limit=limit, before=before, album_id=album_id, q=q)
        items = []
        next_before = None
        for row in rows:
            preview = (
                (row.get("title") or "").strip()
                or (row.get("input_text") or "").strip()[:120]
                or "(фото)"
            )
            items.append(
                TaskListItem(
                    id=row["id"],
                    status=row.get("status") or "done",
                    input_kind=row.get("input_kind") or "text",
                    preview=preview,
                    thumbnail_url=None,   # skip per-row signed URLs (unused) — was up to N Storage calls
                    created_at=row["created_at"],
                )
            )
        if len(rows) == limit and rows:
            next_before = rows[-1]["created_at"]
        return TaskList(items=items, next_before=next_before)
