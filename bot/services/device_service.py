"""Device-token registration for push notifications."""

from __future__ import annotations

from bot.schemas.device import RegisterDeviceRequest
from bot.supabase_service import SupabaseService


class DeviceService:
    def __init__(self, db: SupabaseService):
        self.db = db

    async def register(self, user_id: str, req: RegisterDeviceRequest) -> str:
        return await self.db.upsert_user_device(
            user_id=user_id,
            platform=req.platform,
            token=req.token,
            app_version=req.app_version,
            locale=req.locale,
        )

    async def unregister(self, user_id: str, token: str) -> None:
        await self.db.delete_user_device(user_id=user_id, token=token)
