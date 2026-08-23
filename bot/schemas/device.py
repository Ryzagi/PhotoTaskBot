from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class RegisterDeviceRequest(BaseModel):
    platform: Literal["ios", "android"]
    token: str
    app_version: str | None = None
    locale: str | None = None


class Device(BaseModel):
    id: UUID
