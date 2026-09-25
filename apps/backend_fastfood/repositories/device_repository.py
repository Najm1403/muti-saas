from __future__ import annotations
# repositories/device_repository.py

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.branch import Branch
from models.device import Device, DeviceStatus
from models.business import Business


class DeviceRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _scoped(self, tenant_id: UUID):
        """Base stmt scoped to tenant via Device → Branch → Business join."""
        return (
            select(Device)
            .join(Branch, Device.branch_id == Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .where(
                Business.tenant_id == tenant_id,
                Business.deleted_at.is_(None),
                Branch.deleted_at.is_(None),
                Device.deleted_at.is_(None),
            )
        )

    async def get_by_id(self, id: UUID, tenant_id: UUID) -> Device | None:
        result = await self.db.execute(
            self._scoped(tenant_id).where(Device.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(
        self, branch_id: UUID, device_code: str, tenant_id: UUID
    ) -> Device | None:
        result = await self.db.execute(
            self._scoped(tenant_id).where(
                Device.branch_id == branch_id,
                Device.device_code == device_code,
            )
        )
        return result.scalar_one_or_none()

    async def list(self, branch_id: UUID, tenant_id: UUID) -> list[Device]:
        result = await self.db.execute(
            self._scoped(tenant_id).where(Device.branch_id == branch_id)
        )
        return list(result.scalars().all())

    async def list_for_tenant(
        self, tenant_id: UUID, branch_id: UUID | None = None
    ) -> list[tuple[Device, str, str]]:
        """Every device for a tenant with (device, branch_name, branch_code)."""
        stmt = (
            select(Device, Branch.name, Branch.branch_code)
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
        if branch_id is not None:
            stmt = stmt.where(Device.branch_id == branch_id)
        rows = await self.db.execute(stmt)
        return [(d, bn, bc) for d, bn, bc in rows.all()]

    async def count_all_for_branch(self, branch_id: UUID) -> int:
        """Every device ever created at this branch, including soft-deleted —
        the basis for the next device's letter, so a letter is never reused
        even if an earlier device was deleted."""
        result = await self.db.execute(
            select(func.count(Device.id)).where(Device.branch_id == branch_id)
        )
        return int(result.scalar_one() or 0)

    async def count_billable_for_tenant(self, tenant_id: UUID) -> int:
        """Devices that count against the plan limit (everything except REVOKED)."""
        result = await self.db.execute(
            select(func.count(Device.id))
            .select_from(Device)
            .join(Branch, Device.branch_id == Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .where(
                Business.tenant_id == tenant_id,
                Business.deleted_at.is_(None),
                Branch.deleted_at.is_(None),
                Device.deleted_at.is_(None),
                Device.status != DeviceStatus.REVOKED,
            )
        )
        return int(result.scalar_one() or 0)

    async def get_by_activation_hash(self, code_hash: str) -> Device | None:
        """Global lookup by activation-code hash (used by POS activation, no tenant scope)."""
        result = await self.db.execute(
            select(Device).where(
                Device.activation_code_hash == code_hash,
                Device.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        branch_id: UUID,
        tenant_id: UUID,
        device_code: str,
        letter: str,
        name: str,
        device_type: str = "POS",
    ) -> Device:
        if await self.get_by_code(branch_id, device_code, tenant_id):
            raise ValueError(
                f"Device code '{device_code}' already exists in this branch."
            )
        device = Device(
            id=uuid4(),
            branch_id=branch_id,
            device_code=device_code,
            letter=letter,
            name=name,
            device_type=device_type,
            status=DeviceStatus.PENDING,
        )
        self.db.add(device)
        await self.db.flush()
        await self.db.refresh(device)
        return device

    async def update(self, id: UUID, tenant_id: UUID, **fields) -> Device | None:
        device = await self.get_by_id(id, tenant_id)
        if not device:
            return None
        for key, value in fields.items():
            setattr(device, key, value)
        await self.db.flush()
        await self.db.refresh(device)
        return device

    async def soft_delete(self, id: UUID, tenant_id: UUID) -> bool:
        device = await self.get_by_id(id, tenant_id)
        if not device:
            return False
        device.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True
