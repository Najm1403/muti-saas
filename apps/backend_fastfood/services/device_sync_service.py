# services/device_sync_service.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.branch import Branch
from models.device import Device
from models.business import Business
from schemas.device import DeviceSyncResponse


def _sync_status(last_sync_at: datetime | None) -> str:
    if last_sync_at is None:
        return "never"
    now = datetime.now(timezone.utc)
    age = now - last_sync_at
    if age < timedelta(hours=1):
        return "healthy"
    if age < timedelta(hours=24):
        return "stale"
    return "offline"


class DeviceSyncService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_all(self, tenant_id: UUID) -> list[DeviceSyncResponse]:
        q = await self.db.execute(
            select(Device, Branch.name.label("branch_name"), Branch.branch_code)
            .join(Branch, Device.branch_id == Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .where(
                Business.tenant_id == tenant_id,
                Business.deleted_at.is_(None),
                Branch.deleted_at.is_(None),
                Device.deleted_at.is_(None),
            )
            .order_by(Branch.name, Device.name)
        )
        result = []
        for device, branch_name, branch_code in q.all():
            result.append(DeviceSyncResponse(
                id=device.id,
                branch_id=device.branch_id,
                branch_name=branch_name,
                branch_code=branch_code,
                name=device.name,
                device_code=device.device_code,
                device_type=device.device_type,
                status=device.status,
                is_active=device.is_active,
                is_activated=device.is_activated,
                activated_at=device.activated_at,
                last_sync_at=device.last_sync_at,
                sync_status=_sync_status(device.last_sync_at),
                created_at=device.created_at,
                updated_at=device.updated_at,
            ))
        return result
