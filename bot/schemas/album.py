from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AlbumCreate(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    emoji: str | None = Field(default=None, max_length=8)
    color: str | None = None  # palette key


class AlbumUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=60)
    emoji: str | None = Field(default=None, max_length=8)
    color: str | None = None


class Album(BaseModel):
    id: UUID
    name: str
    emoji: str | None = None
    color: str | None = None
    task_count: int = 0
    updated_at: datetime


class AlbumList(BaseModel):
    items: list[Album]


class AssignAlbumRequest(BaseModel):
    album_id: UUID | None = None  # null detaches the task from any album
