"""Album (theme collection) operations."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from bot.schemas.album import Album
from bot.supabase_service import SupabaseService


def _to_album(row: dict) -> Album:
    updated = row.get("last_updated") or row.get("updated_at")
    if isinstance(updated, str):
        updated = datetime.fromisoformat(updated.replace("Z", "+00:00"))
    return Album(
        id=UUID(row["id"]) if isinstance(row["id"], str) else row["id"],
        name=row["name"],
        emoji=row.get("emoji"),
        color=row.get("color"),
        task_count=int(row.get("task_count", 0)),
        updated_at=updated,
    )


class AlbumService:
    def __init__(self, db: SupabaseService):
        self.db = db

    async def list(self, user_id: str) -> list[Album]:
        return [_to_album(r) for r in await self.db.list_albums(user_id)]

    async def create(self, user_id: str, name: str, emoji: str | None, color: str | None) -> Album:
        return _to_album(await self.db.create_album(user_id, name, emoji, color))

    async def update(self, user_id: str, album_id: UUID, fields: dict) -> Album | None:
        row = await self.db.update_album(user_id, album_id, fields)
        return _to_album(row) if row else None

    async def delete(self, user_id: str, album_id: UUID) -> None:
        await self.db.delete_album(user_id, album_id)

    async def assign(self, user_id: str, task_id: str, album_id: UUID | None) -> bool:
        return await self.db.assign_task_album(user_id, task_id, album_id)
