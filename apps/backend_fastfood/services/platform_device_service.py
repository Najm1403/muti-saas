# services/platform_device_service.py
#
# Cross-tenant device controls for platform admins: emergency suspend / revoke.
# A PLATFORM suspension cannot be lifted by the tenant (only a platform admin here).

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import NotFoundError, ValidationError
from models.device import Device, DeviceStatus, SuspendScope
from schemas.device import DeviceResponse


class PlatformDeviceService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _get_or_404(self, device_id: UUID) -> Device:
        result = await self.db.execute(
            select(Device).where(Device.id == device_id, Device.deleted_at.is_(None))
        )
        device = result.scalar_one_or_none()
        if not device:
            raise NotFoundError("Device not found.")
        return device

    async def suspend(self, device_id: UUID) -> DeviceResponse:
        device = await self._get_or_404(device_id)
        if device.status == DeviceStatus.REVOKED:
            raise ValidationError("Device is revoked.")
        device.status = DeviceStatus.SUSPENDED
        device.suspended_scope = SuspendScope.PLATFORM
        await self.db.commit()
        await self.db.refresh(device)
        return DeviceResponse.model_validate(device)

    async def reactivate(self, device_id: UUID) -> DeviceResponse:
        device = await self._get_or_404(device_id)
        if device.status == DeviceStatus.REVOKED:
            raise ValidationError("A revoked device cannot be reactivated.")
        if device.status != DeviceStatus.SUSPENDED:
            raise ValidationError("Only a suspended device can be reactivated.")
        device.status = DeviceStatus.ACTIVE
        device.suspended_scope = None
        await self.db.commit()
        await self.db.refresh(device)
        return DeviceResponse.model_validate(device)

    async def revoke(self, device_id: UUID) -> DeviceResponse:
        device = await self._get_or_404(device_id)
        if device.status == DeviceStatus.REVOKED:
            raise ValidationError("Device is already revoked.")
        device.status = DeviceStatus.REVOKED
        device.suspended_scope = None
        device.revoked_at = datetime.now(timezone.utc)
        device.activation_code_hash = None
        device.activation_code = None
        device.activation_code_expires_at = None
        await self.db.commit()
        await self.db.refresh(device)
        return DeviceResponse.model_validate(device)
