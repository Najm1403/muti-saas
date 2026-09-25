from __future__ import annotations
# repositories/branch_repository.py

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.branch import Branch
from models.business import Business


class BranchRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _scoped(self, tenant_id: UUID):
        """Base stmt scoped to tenant via Branch → Business join."""
        return (
            select(Branch)
            .join(Business, Branch.business_id == Business.id)
            .where(
                Business.tenant_id == tenant_id,
                Business.deleted_at.is_(None),
                Branch.deleted_at.is_(None),
            )
        )

    async def get_by_id(self, id: UUID, tenant_id: UUID) -> Branch | None:
        result = await self.db.execute(
            self._scoped(tenant_id).where(Branch.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(
        self, business_id: UUID, branch_code: str, tenant_id: UUID
    ) -> Branch | None:
        result = await self.db.execute(
            self._scoped(tenant_id).where(
                Branch.business_id == business_id,
                Branch.branch_code == branch_code,
            )
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        business_id: UUID,
        tenant_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Branch]:
        stmt = (
            self._scoped(tenant_id)
            .where(Branch.business_id == business_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        business_id: UUID,
        tenant_id: UUID,
        branch_code: str,
        name: str,
        address: str | None = None,
        phone: str | None = None,
    ) -> Branch:
        if await self.get_by_code(business_id, branch_code, tenant_id):
            raise ValueError(
                f"Branch code '{branch_code}' already exists in this business."
            )
        branch = Branch(
            id=uuid4(),
            business_id=business_id,
            branch_code=branch_code,
            name=name,
            address=address,
            phone=phone,
        )
        self.db.add(branch)
        await self.db.flush()
        await self.db.refresh(branch)
        return branch

    async def update(self, id: UUID, tenant_id: UUID, **fields) -> Branch | None:
        branch = await self.get_by_id(id, tenant_id)
        if not branch:
            return None
        for key, value in fields.items():
            setattr(branch, key, value)
        await self.db.flush()
        await self.db.refresh(branch)
        return branch

    async def soft_delete(self, id: UUID, tenant_id: UUID) -> bool:
        branch = await self.get_by_id(id, tenant_id)
        if not branch:
            return False
        branch.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True
