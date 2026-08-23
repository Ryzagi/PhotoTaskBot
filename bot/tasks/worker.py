"""arq worker entry point.

Usage:
    arq bot.tasks.worker.WorkerSettings
"""

from __future__ import annotations

import os
from typing import ClassVar

from arq.connections import RedisSettings  # type: ignore[import-not-found]

from bot.tasks.jobs import solve_image_task, solve_text_task


async def startup(ctx: dict) -> None:
    from bot.app.deps import build_worker_context

    ctx.update(await build_worker_context())


async def shutdown(ctx: dict) -> None:
    db = ctx.get("db")
    if db and hasattr(db, "close"):
        await db.close()


class WorkerSettings:
    functions: ClassVar = [solve_image_task, solve_text_task]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(os.environ.get("REDIS_URL", "redis://localhost:6379"))
    max_tries = 2
    job_timeout = 120
    keep_result = 60
