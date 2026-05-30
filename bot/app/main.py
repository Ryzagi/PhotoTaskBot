"""New unified FastAPI entrypoint.

Mounts both the legacy bot endpoints (/tasker/api/*) and the new mobile
endpoints (/v1/* and /internal/*). The legacy app is preserved so the
Telegram bot keeps working through the transition; once it's been migrated
to /internal/*, the legacy routes can be removed.

Run with:
    uvicorn bot.app.main:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import structlog
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from bot.api.internal import router as internal_router
from bot.api.v1 import router as v1_router
from bot.app.app import app as legacy_app  # keep the bot working
from bot.schemas.errors import make as make_error

load_dotenv()
log = structlog.get_logger(__name__)

app = FastAPI(
    title="PandaSolve API",
    version="0.2.0",
    description=(
        "Backend for the PandaSolve / PhotoTaskBot product. "
        "Mobile clients use /v1/*; the Telegram bot uses /internal/*."
    ),
)


# Standard error envelope.
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_request, exc: StarletteHTTPException):
    code = {
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        413: "image_too_large",
        429: "rate_limited",
    }.get(exc.status_code, "internal_error")
    return JSONResponse(
        make_error(code, str(exc.detail)),
        status_code=exc.status_code,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request, exc: RequestValidationError):
    return JSONResponse(
        make_error("validation_failed", "Validation failed.", {"errors": exc.errors()}),
        status_code=422,
    )


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


app.include_router(v1_router)
app.include_router(internal_router)

# Mount the legacy app LAST so /tasker/api/* keeps responding, but only as a
# fallback — /v1/*, /internal/* and /healthz are matched first.
app.mount("/", legacy_app)
