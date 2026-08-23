"""arq jobs that perform the actual solve and persist the result.

Task ids are the DB-assigned bigint surfaced as strings; user ids are text.
"""

from __future__ import annotations

import io

import structlog
from arq import Retry  # type: ignore[import-not-found]

log = structlog.get_logger(__name__)


async def solve_image_task(ctx: dict, task_id: str) -> None:
    db = ctx["db"]
    gpt = ctx["gpt"]
    gemini = ctx["gemini"]
    push = ctx["push"]
    billing = ctx["billing"]

    task = await db.get_task(task_id)
    if task is None or task["status"] != "pending":
        return

    image_bytes = await db.download_object(task["image_path"])

    try:
        solution = await gpt.solve(io.BytesIO(image_bytes), caption=task.get("input_text"))
        model = "gpt-5-mini"
    except _RetryableSolverError as e:
        raise Retry(defer=ctx.get("job_try", 1) * 10) from e
    except Exception as e:
        log.warning("solve.gpt_failed", task_id=task_id, error=str(e))
        try:
            solution = await gemini.solve(io.BytesIO(image_bytes), caption=task.get("input_text"))
            model = "gemini-2.5-flash"
        except Exception as e2:
            log.error("solve.both_failed", task_id=task_id, error=str(e2))
            await db.mark_task_failed(task_id, error_code="solver_failed", detail=str(e2))
            await billing.refund(task["user_id"], task.get("spent_from") or "daily")
            await push.send(task["user_id"], "task.failed", {
                "title": "Не удалось решить задачу",
                "body": "Попробуй еще раз позже.",
                "task_id": task_id,
            })
            return

    await db.mark_task_done(task_id, solution=solution, model_used=model)
    preview = solution["solutions"][0]["problem"][:120] if solution.get("solutions") else "Solved"
    await push.send(task["user_id"], "task.completed", {
        "title": "Решение готово",
        "body": preview,
        "task_id": task_id,
    })


async def solve_text_task(ctx: dict, task_id: str) -> None:
    db = ctx["db"]
    gpt = ctx["gpt"]
    gemini = ctx["gemini"]
    push = ctx["push"]
    billing = ctx["billing"]

    task = await db.get_task(task_id)
    if task is None or task["status"] != "pending":
        return

    try:
        solution = await gpt.generate_text_solution(task["input_text"])
        model = "gpt-5-mini"
    except Exception as e:
        log.warning("solve_text.gpt_failed", task_id=task_id, error=str(e))
        try:
            solution = await gemini.generate_text(task["input_text"])
            model = "gemini-2.5-flash"
        except Exception as e2:
            log.error("solve_text.both_failed", task_id=task_id, error=str(e2))
            await db.mark_task_failed(task_id, error_code="solver_failed", detail=str(e2))
            await billing.refund(task["user_id"], task.get("spent_from") or "daily")
            return

    await db.mark_task_done(task_id, solution=solution, model_used=model)
    preview = solution["solutions"][0]["problem"][:120] if solution.get("solutions") else "Solved"
    await push.send(task["user_id"], "task.completed", {
        "title": "Решение готово",
        "body": preview,
        "task_id": task_id,
    })


class _RetryableSolverError(Exception):
    pass
