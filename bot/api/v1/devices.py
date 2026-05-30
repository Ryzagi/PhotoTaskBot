"""Device-token registration for push."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from fastapi.responses import Response

from bot.app.deps import get_device_service
from bot.auth.dependencies import current_user
from bot.schemas.device import Device, RegisterDeviceRequest
from bot.services.device_service import DeviceService

router = APIRouter(tags=["devices"])


@router.post("/devices", response_model=Device, status_code=status.HTTP_201_CREATED)
async def register_device(
    payload: RegisterDeviceRequest,
    user=Depends(current_user),
    devices: DeviceService = Depends(get_device_service),
) -> Device:
    device_id = await devices.register(user.id, payload)
    return Device(id=device_id)


@router.delete("/devices/{token}", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_device(
    token: str,
    user=Depends(current_user),
    devices: DeviceService = Depends(get_device_service),
) -> Response:
    await devices.unregister(user.id, token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
