# api/v1/devices.py
#
# Tenant-owned POS device management.
#
#   Tenant → Restaurant → Branch → Device
#
# The tenant admin creates a device (name + branch + purpose) and gets a one-time
# 4-digit activation code. The physical device pairs itself via
# POST /api/v1/pos/auth/activate. Lifecycle actions: suspend / reactivate / revoke.
#
# Prefix: /api/v1/devices

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentUser, get_current_user
from db.session import get_db
from schemas.common import MessageResponse
from schemas.device import (
    ActivationCodeView,
    DeviceCreate,
    DeviceCreatedResponse,
    DeviceListItem,
    DeviceResponse,
    DeviceSyncResponse,
    DeviceUpdate,
)
from services.device_service import DeviceService
from services.device_sync_service import DeviceSyncService

router = APIRouter(prefix="/devices", tags=["Devices"])


def _svc(db: AsyncSession = Depends(get_db)) -> DeviceService:
    return DeviceService(db)


def _sync_svc(db: AsyncSession = Depends(get_db)) -> DeviceSyncService:
    return DeviceSyncService(db)


@router.get(
    "/",
    response_model=list[DeviceListItem],
    status_code=status.HTTP_200_OK,
    summary="List devices",
    description="Every device across the tenant's branches. Optional ?branch_id= filter.",
)
@router.get("", response_model=list[DeviceListItem], status_code=status.HTTP_200_OK, include_in_schema=False)
async def list_devices(
    branch_id: UUID | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    svc: DeviceService = Depends(_svc),
) -> list[DeviceListItem]:
    rows = await svc.list(tenant_id=current_user.tenant_id, branch_id=branch_id)
    from api.branch_access import visible_branches
    allowed = await visible_branches(svc.db, current_user)
    return rows if allowed is None else [row for row in rows if row.branch_id in allowed]


@router.get(
    "/limits",
    status_code=status.HTTP_200_OK,
    summary="Device usage vs plan limit",
    description="{ used, limit } — limit -1 means unlimited.",
)
async def device_limits(
    current_user: CurrentUser = Depends(get_current_user),
    svc: DeviceService = Depends(_svc),
) -> dict:
    return await svc.limits(tenant_id=current_user.tenant_id)


@router.post(
    "/",
    response_model=DeviceCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add device",
    description=(
        "Registers a device under a branch and returns a one-time 4-digit activation "
        "code (valid 15 minutes). Returns 409 if the plan's device limit is reached."
    ),
)
@router.post("", response_model=DeviceCreatedResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_device(
    data: DeviceCreate,
    current_user: CurrentUser = Depends(get_current_user),
    svc: DeviceService = Depends(_svc),
) -> DeviceCreatedResponse:
    return await svc.create(tenant_id=current_user.tenant_id, data=data)


@router.get(
    "/sync-health",
    response_model=list[DeviceSyncResponse],
    status_code=status.HTTP_200_OK,
    summary="Sync health for all devices",
)
async def list_device_sync_health(
    current_user: CurrentUser = Depends(get_current_user),
    svc: DeviceSyncService = Depends(_sync_svc),
) -> list[DeviceSyncResponse]:
    rows = await svc.list_all(tenant_id=current_user.tenant_id)
    from api.branch_access import visible_branches
    allowed = await visible_branches(svc.db, current_user)
    return rows if allowed is None else [row for row in rows if row.branch_id in allowed]


@router.get(
    "/{id}",
    response_model=DeviceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get device",
)
async def get_device(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: DeviceService = Depends(_svc),
) -> DeviceResponse:
    return await svc.get(id=id, tenant_id=current_user.tenant_id)


@router.patch(
    "/{id}",
    response_model=DeviceResponse,
    status_code=status.HTTP_200_OK,
    summary="Update device",
    description="Rename or change the device purpose. Lifecycle uses the dedicated endpoints.",
)
async def update_device(
    id: UUID,
    data: DeviceUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    svc: DeviceService = Depends(_svc),
) -> DeviceResponse:
    return await svc.update(id=id, tenant_id=current_user.tenant_id, data=data)


@router.get(
    "/{id}/activation-code",
    response_model=ActivationCodeView,
    status_code=status.HTTP_200_OK,
    summary="Show the current activation code",
    description=(
        "Re-displays a pending device's activation code while it is still valid. "
        "`used` = the device is already activated (use reset instead); "
        "`expired` = the last code lapsed (generate a new one)."
    ),
)
async def show_activation_code(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: DeviceService = Depends(_svc),
) -> ActivationCodeView:
    return await svc.get_code(id=id, tenant_id=current_user.tenant_id)


@router.post(
    "/{id}/activation-code",
    response_model=DeviceCreatedResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a new activation code",
    description=(
        "Issues a fresh 4-digit code for a device that has not been activated yet. "
        "Returns 409 if the device is already activated — reset it first."
    ),
)
async def regenerate_activation_code(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: DeviceService = Depends(_svc),
) -> DeviceCreatedResponse:
    return await svc.regenerate_code(id=id, tenant_id=current_user.tenant_id)


@router.post(
    "/{id}/reset",
    response_model=DeviceCreatedResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset (unpair) an activated device",
    description=(
        "Unpairs an activated device and issues a new activation code. The old "
        "install stops working on its next contact with the server; the same or a "
        "different device can be paired again with the new code. The device keeps "
        "its slot against the plan limit."
    ),
)
async def reset_device(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: DeviceService = Depends(_svc),
) -> DeviceCreatedResponse:
    return await svc.reset(id=id, tenant_id=current_user.tenant_id)


@router.post(
    "/{id}/suspend",
    response_model=DeviceResponse,
    status_code=status.HTTP_200_OK,
    summary="Suspend device",
    description="Blocks the device on its next contact with the server. Reversible.",
)
async def suspend_device(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: DeviceService = Depends(_svc),
) -> DeviceResponse:
    return await svc.suspend(id=id, tenant_id=current_user.tenant_id)


@router.post(
    "/{id}/reactivate",
    response_model=DeviceResponse,
    status_code=status.HTTP_200_OK,
    summary="Reactivate device",
    description="Only for a device suspended by the tenant (not a platform suspension).",
)
async def reactivate_device(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: DeviceService = Depends(_svc),
) -> DeviceResponse:
    return await svc.reactivate(id=id, tenant_id=current_user.tenant_id)


@router.post(
    "/{id}/revoke",
    response_model=DeviceResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke device",
    description="Permanently kills the device's access. Cannot be undone — add a new device instead.",
)
async def revoke_device(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: DeviceService = Depends(_svc),
) -> DeviceResponse:
    return await svc.revoke(id=id, tenant_id=current_user.tenant_id)


@router.delete(
    "/{id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete device",
    description="Soft-deletes the device. Historical sales are retained.",
)
async def delete_device(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: DeviceService = Depends(_svc),
) -> MessageResponse:
    await svc.delete(id=id, tenant_id=current_user.tenant_id)
    return MessageResponse(message="Device deleted.")
