"""Bot-facing internal API. HMAC-authenticated, may change without notice."""

from fastapi import APIRouter

from bot.api.internal import link, solve, users

# HMAC auth is enforced by InternalAuthMiddleware (it must read the raw body
# before FastAPI parses Form()/File() — a dependency can't, see that module).
router = APIRouter(prefix="/internal")
router.include_router(link.router)
router.include_router(solve.router)
router.include_router(users.router)
