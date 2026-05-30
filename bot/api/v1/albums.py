"""Album endpoints — theme collections of tasks."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from bot.app.deps import get_album_service
from bot.auth.dependencies import current_user
from bot.schemas.album import Album, AlbumCreate, AlbumList, AlbumUpdate, AssignAlbumRequest
from bot.services.album_service import AlbumService

router = APIRouter(tags=["albums"])


@router.get("/albums", response_model=AlbumList)
async def list_albums(
    user=Depends(current_user),
    albums: AlbumService = Depends(get_album_service),
) -> AlbumList:
    return AlbumList(items=await albums.list(user.id))


@router.post("/albums", response_model=Album, status_code=status.HTTP_201_CREATED)
async def create_album(
    payload: AlbumCreate,
    user=Depends(current_user),
    albums: AlbumService = Depends(get_album_service),
) -> Album:
    return await albums.create(user.id, payload.name, payload.emoji, payload.color)


@router.patch("/albums/{album_id}", response_model=Album)
async def update_album(
    album_id: UUID,
    payload: AlbumUpdate,
    user=Depends(current_user),
    albums: AlbumService = Depends(get_album_service),
) -> Album:
    updated = await albums.update(user.id, album_id, payload.model_dump(exclude_none=True))
    if not updated:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="album not found")
    return updated


@router.delete("/albums/{album_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_album(
    album_id: UUID,
    user=Depends(current_user),
    albums: AlbumService = Depends(get_album_service),
) -> Response:
    await albums.delete(user.id, album_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/tasks/{task_id}/album", status_code=status.HTTP_200_OK)
async def assign_task_to_album(
    task_id: str,
    payload: AssignAlbumRequest,
    user=Depends(current_user),
    albums: AlbumService = Depends(get_album_service),
) -> dict:
    ok = await albums.assign(user.id, task_id, payload.album_id)
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="task not found")
    return {"task_id": str(task_id), "album_id": str(payload.album_id) if payload.album_id else None}
