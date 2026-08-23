"""Album schema validation + presence in the v1 surface."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from bot.schemas.album import Album, AlbumCreate, AlbumList, AssignAlbumRequest


def test_album_create_requires_name():
    with pytest.raises(ValidationError):
        AlbumCreate(name="")


def test_album_create_minimal():
    a = AlbumCreate(name="Математика")
    assert a.emoji is None and a.color is None


def test_album_roundtrip():
    a = Album(id=uuid4(), name="Геометрия", emoji="📐", color="lav", task_count=7,
              updated_at=datetime.now(UTC))
    AlbumList(items=[a]).model_validate(AlbumList(items=[a]).model_dump(mode="json"))


def test_assign_allows_null():
    AssignAlbumRequest(album_id=None)
    AssignAlbumRequest(album_id=uuid4())


def test_albums_in_v1_openapi():
    pytest.importorskip("fastapi")
    from fastapi import FastAPI

    from bot.api.v1 import router as v1_router

    app = FastAPI()
    app.include_router(v1_router)
    paths = set(app.openapi()["paths"].keys())
    assert "/v1/albums" in paths
    assert "/v1/tasks/{task_id}/album" in paths
