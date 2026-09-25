from __future__ import annotations
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.permission import Permission
from models.role import Role
from models.role_permission import RolePermission


class RoleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, id: UUID, tenant_id: UUID) -> Role | None:
        stmt = select(Role).where(
            Role.id == id,
            Role.tenant_id == tenant_id,
            Role.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, tenant_id: UUID) -> list[Role]:
        stmt = select(Role).where(Role.tenant_id == tenant_id, Role.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self, tenant_id: UUID, name: str, description: str | None = None
    ) -> Role:
        stmt = select(Role).where(
            Role.tenant_id == tenant_id,
            Role.name == name,
            Role.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise ValueError(f"Role '{name}' already exists in tenant '{tenant_id}'.")
        role = Role(id=uuid4(), tenant_id=tenant_id, name=name, description=description)
        self.db.add(role)
        await self.db.flush()
        await self.db.refresh(role)
        return role

    async def update(self, id: UUID, tenant_id: UUID, **fields) -> Role | None:
        role = await self.get_by_id(id, tenant_id)
        if not role:
            return None
        for key, value in fields.items():
            setattr(role, key, value)
        await self.db.flush()
        await self.db.refresh(role)
        return role

    async def soft_delete(self, id: UUID, tenant_id: UUID) -> bool:
        role = await self.get_by_id(id, tenant_id)
        if not role:
            return False
        role.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True

    async def assign_permission(self, role_id: UUID, permission_id: UUID) -> RolePermission:
        stmt = select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id,
            RolePermission.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            return existing
        rp = RolePermission(id=uuid4(), role_id=role_id, permission_id=permission_id)
        self.db.add(rp)
        await self.db.flush()
        await self.db.refresh(rp)
        return rp

    async def remove_permission(self, role_id: UUID, permission_id: UUID) -> bool:
        stmt = select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id,
            RolePermission.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        rp = result.scalar_one_or_none()
        if not rp:
            return False
        rp.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True

    async def get_permissions(self, role_id: UUID) -> list[Permission]:
        stmt = (
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(
                RolePermission.role_id == role_id,
                RolePermission.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
