# api/platform/devices.py
#
# Platform-wide device visibility + emergency controls.
# Devices are created by tenants (POST /api/v1/devices); the platform admin can
# list every device and suspend / reactivate / revoke one in an emergency.
# A platform suspension cannot be lifted by the tenant.
#
# Prefix: /api/platform/devices

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.platform.dependencies import CurrentPlatformAdmin, get_current_platform_admin
from db.session import get_db
from schemas.device import DeviceResponse
from schemas.onboarding import DeviceHealthResponse
from services.onboarding_service import OnboardingService
from services.platform_device_service import PlatformDeviceService

router = APIRouter(prefix="/devices", tags=["Platform · Devices"])


def _svc(db: AsyncSession = Depends(get_db)) -> PlatformDeviceService:
    return PlatformDeviceService(db)


def _ob_svc(db: AsyncSession = Depends(get_db)) -> OnboardingService:
    return OnboardingService(db)


@router.get(
    "",
    response_model=list[DeviceHealthResponse],
    status_code=status.HTTP_200_OK,
    summary="List all devices (all tenants)",
)
@router.get("/", response_model=list[DeviceHealthResponse], status_code=status.HTTP_200_OK, include_in_schema=False)
async def list_all_devices(
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: OnboardingService = Depends(_ob_svc),
) -> list[DeviceHealthResponse]:
    return await svc.list_all_devices()


@router.post(
    "/{device_id}/suspend",
    response_model=DeviceResponse,
    status_code=status.HTTP_200_OK,
    summary="Emergency suspend a device",
    description="Blocks the device on its next contact with the server. The tenant cannot lift this.",
)
async def suspend_device(
    device_id: UUID,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: PlatformDeviceService = Depends(_svc),
) -> DeviceResponse:
    return await svc.suspend(device_id)


@router.post(
    "/{device_id}/reactivate",
    response_model=DeviceResponse,
    status_code=status.HTTP_200_OK,
    summary="Lift a suspension",
)
async def reactivate_device(
    device_id: UUID,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: PlatformDeviceService = Depends(_svc),
) -> DeviceResponse:
    return await svc.reactivate(device_id)


@router.post(
    "/{device_id}/revoke",
    response_model=DeviceResponse,
    status_code=status.HTTP_200_OK,
    summary="Emergency revoke a device",
    description="Permanently kills the device's access. Cannot be undone.",
)
async def revoke_device(
    device_id: UUID,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: PlatformDeviceService = Depends(_svc),
) -> DeviceResponse:
    return await svc.revoke(device_id)
