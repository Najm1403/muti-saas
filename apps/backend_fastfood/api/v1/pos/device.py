# api/v1/pos/device.py
#
# POS device management endpoints.
# Heartbeat: the app calls this periodically to signal it is online
# and to update last_sync_at on the device record.
#
# Prefix: /api/v1/pos/device

from __future__ import annotations
from api.v1.pos._guards import operational_device

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentDevice
from core.exceptions import NotFoundError
from db.session import get_db
from models.branch import Branch
from models.device import Device, assert_operational
from models.business import Business
from schemas.common import MessageResponse

router = APIRouter(prefix="/device", tags=["POS — Device"])


@router.patch(
    "/heartbeat",
    response_model=MessageResponse,
    summary="Device heartbeat",
    description=(
        "Called by the POS app after every successful sync or on a fixed interval. "
        "Updates last_sync_at on the device so the tenant dashboard can show "
        "which devices are online and when they last synced."
    ),
)
async def heartbeat(
    device: CurrentDevice = Depends(operational_device),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    # GAP 1 — join through Branch → Business so a crafted JWT with a
    # device_id belonging to another tenant cannot update that device's heartbeat.
    result = await db.execute(
        select(Device)
        .join(Branch, Device.branch_id == Branch.id)
        .join(Business, Branch.business_id == Business.id)
        .where(
            Device.id == device.device_id,
            Device.branch_id == device.branch_id,
            Business.tenant_id == device.tenant_id,
            Device.deleted_at.is_(None),
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise NotFoundError("Device not found.")

    assert_operational(device)  # 403 {code: DEVICE_SUSPENDED | DEVICE_REVOKED}

    device.last_sync_at = datetime.now(timezone.utc)
    await db.commit()
    return MessageResponse(message="Heartbeat recorded.")
