from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.tenant import Tenant


class TenantRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, id: UUID) -> Tenant | None:
        stmt = select(Tenant).where(Tenant.id == id, Tenant.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, tenant_code: str) -> Tenant | None:
        stmt = select(Tenant).where(
            Tenant.tenant_code == tenant_code,
            Tenant.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, skip: int = 0, limit: int = 50) -> list[Tenant]:
        stmt = select(Tenant).where(Tenant.deleted_at.is_(None)).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, name: str, tenant_code: str, business_template_id: UUID, is_active: bool = True) -> Tenant:
        existing = await self.get_by_code(tenant_code)
        if existing:
            raise ValueError(f"Tenant with code '{tenant_code}' already exists.")
        tenant = Tenant(id=uuid4(), name=name, tenant_code=tenant_code,
                         business_template_id=business_template_id, is_active=is_active)
        self.db.add(tenant)
        await self.db.flush()
        await self.db.refresh(tenant)
        return tenant

    async def update(self, id: UUID, **fields) -> Tenant | None:
        tenant = await self.get_by_id(id)
        if not tenant:
            return None
        for key, value in fields.items():
            setattr(tenant, key, value)
        await self.db.flush()
        await self.db.refresh(tenant)
        return tenant

    async def soft_delete(self, id: UUID) -> bool:
        tenant = await self.get_by_id(id)
        if not tenant:
            return False
        tenant.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True

    async def set_active(self, id: UUID, is_active: bool) -> Tenant | None:
        return await self.update(id, is_active=is_active)
