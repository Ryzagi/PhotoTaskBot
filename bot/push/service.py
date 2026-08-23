"""Cross-platform push fan-out."""

from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID

import structlog

from bot.push.apns import APNsClient
from bot.push.apns import UnregisteredError as APNsUnregistered
from bot.push.fcm import FCMClient
from bot.push.fcm import UnregisteredError as FCMUnregistered
from bot.supabase_service import SupabaseService

log = structlog.get_logger(__name__)


def _build_apns(topic: str, payload: dict, locale: str | None) -> dict:
    return {
        "aps": {
            "alert": {
                "title": payload.get("title", "PandaSolve"),
                "body": payload.get("body", ""),
            },
            "sound": "default",
            "badge": 1,
            "mutable-content": 1,
            "thread-id": topic,
        },
        **{k: v for k, v in payload.items() if k not in ("title", "body")},
    }


def _build_fcm(topic: str, payload: dict, locale: str | None) -> dict:
    data = {k: str(v) for k, v in payload.items() if k not in ("title", "body")}
    data["topic"] = topic
    return {
        "notification": {
            "title": payload.get("title", "PandaSolve"),
            "body": payload.get("body", ""),
        },
        "data": data,
        "android": {
            "priority": "high",
            "notification": {"channel_id": "task_updates"},
        },
    }


class PushService:
    def __init__(self, apns: APNsClient, fcm: FCMClient, db: SupabaseService):
        self.apns = apns
        self.fcm = fcm
        self.db = db

    async def send(self, user_id: UUID, topic: str, payload: dict[str, Any]) -> None:
        devices = await self.db.list_user_devices(user_id)
        await asyncio.gather(
            *[self._send_one(d, topic, payload) for d in devices],
            return_exceptions=True,
        )

    async def _send_one(self, device: dict, topic: str, payload: dict) -> None:
        try:
            if device["platform"] == "ios":
                await self.apns.send(device["token"], _build_apns(topic, payload, device.get("locale")))
            else:
                await self.fcm.send(device["token"], _build_fcm(topic, payload, device.get("locale")))
            log.info("push.sent", topic=topic, platform=device["platform"], user_id=str(device["user_id"]))
        except (APNsUnregistered, FCMUnregistered):
            await self.db.delete_user_device_by_token(device["token"])
            log.info("push.token_invalid", platform=device["platform"], token=device["token"][:10])
        except Exception as e:
            log.warning("push.error", topic=topic, platform=device["platform"], error=str(e))
