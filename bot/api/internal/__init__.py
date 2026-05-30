"""Bot-facing internal API. HMAC-authenticated, may change without notice."""

from fastapi import APIRouter, Depends

from bot.api.internal import link, solve, users
from bot.auth.dependencies import verify_internal

router = APIRouter(prefix="/internal", dependencies=[Depends(verify_internal)])
router.include_router(link.router)
router.include_router(solve.router)
router.include_router(users.router)
