"""Application-level dependency wiring.

Centralizes construction of services so both the HTTP app (bot/app/main.py)
and the worker (bot/tasks/worker.py) get the same wiring. FastAPI's Depends()
uses these in its dependency-resolution graph.
"""

from __future__ import annotations

import os
from functools import lru_cache

from arq import create_pool  # type: ignore[import-not-found]
from arq.connections import RedisSettings  # type: ignore[import-not-found]

from bot.gemini_service import GeminiSolver
from bot.gpt_service import TaskSolverGPT
from bot.push.apns import APNsClient, APNsConfig
from bot.push.fcm import FCMClient, FCMConfig
from bot.push.service import PushService
from bot.services.album_service import AlbumService
from bot.services.billing_service import BillingService
from bot.services.device_service import DeviceService
from bot.services.play_billing import PlayBillingService
from bot.services.task_service import TaskService
from bot.services.user_service import UserService
from bot.supabase_service import SupabaseService


def _play_service_account() -> dict | None:
    """Service-account JSON for the Play Developer API. Accepts raw JSON or base64."""
    import base64
    import json

    raw = os.environ.get("GOOGLE_PLAY_SERVICE_ACCOUNT_JSON", "").strip()
    if not raw:
        return None
    try:
        decoded = raw if raw.startswith("{") else base64.b64decode(raw).decode()
        return json.loads(decoded)
    except Exception:
        return None


@lru_cache(maxsize=1)
def get_db() -> SupabaseService:
    return SupabaseService(
        supabase_url=os.environ["SUPABASE_URL"],
        supabase_key=os.environ["SUPABASE_KEY"],
        user_email=os.environ["USER_EMAIL"],
        user_password=os.environ["USER_PASSWORD"],
    )


@lru_cache(maxsize=1)
def get_gpt() -> TaskSolverGPT:
    return TaskSolverGPT(openai_api_key=os.environ["OPENAI_API_KEY"])


@lru_cache(maxsize=1)
def get_gemini() -> GeminiSolver:
    return GeminiSolver(google_api_key=os.environ["GOOGLE_API_KEY"])


@lru_cache(maxsize=1)
def get_push() -> PushService:
    return PushService(
        apns=APNsClient(APNsConfig.from_env()),
        fcm=FCMClient(FCMConfig.from_env()),
        db=get_db(),
    )


def get_billing() -> BillingService:
    return BillingService(db=get_db())


@lru_cache(maxsize=1)
def get_play_billing() -> PlayBillingService:
    return PlayBillingService(
        db=get_db(),
        billing=get_billing(),
        package_name=os.environ.get("GOOGLE_PLAY_PACKAGE_NAME", ""),
        sa_info=_play_service_account(),
    )


def get_user_service() -> UserService:
    return UserService(db=get_db())


def get_device_service() -> DeviceService:
    return DeviceService(db=get_db())


def get_album_service() -> AlbumService:
    return AlbumService(db=get_db())


_arq_pool = None
_queue_disabled = False


async def get_queue():
    """Return an arq pool, or None if Redis isn't reachable — in which case the
    solve runs inline in the request (fine for a single-box dev setup)."""
    global _arq_pool, _queue_disabled
    if _queue_disabled:
        return None
    if _arq_pool is None:
        try:
            _arq_pool = await create_pool(
                RedisSettings.from_dsn(os.environ.get("REDIS_URL", "redis://localhost:6379"))
            )
        except Exception:
            _queue_disabled = True
            return None
    return _arq_pool


async def get_task_service() -> TaskService:
    return TaskService(
        db=get_db(),
        billing=get_billing(),
        queue=await get_queue(),
        gpt=get_gpt(),
        gemini=get_gemini(),
    )


async def build_worker_context() -> dict:
    """Used by arq worker startup (bot/tasks/worker.py)."""
    return {
        "db": get_db(),
        "gpt": get_gpt(),
        "gemini": get_gemini(),
        "push": get_push(),
        "billing": get_billing(),
    }
