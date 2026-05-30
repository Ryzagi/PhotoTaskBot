"""Mobile-facing API surface (JWT-authenticated, stable)."""

from fastapi import APIRouter

from bot.api.v1 import albums, config, devices, link, me, tasks

router = APIRouter(prefix="/v1")
router.include_router(me.router)
router.include_router(devices.router)
router.include_router(tasks.router)
router.include_router(albums.router)
router.include_router(link.router)
router.include_router(config.router)
