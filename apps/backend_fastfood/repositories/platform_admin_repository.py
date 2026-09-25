# repositories/platform_admin_repository.py
#
# Data-access layer for PlatformAdmin.
# No tenant_id scoping — platform admins are cross-tenant by design.

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.platform_admin import PlatformAdmin


class PlatformAdminRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, id: UUID) -> PlatformAdmin | None:
        result = await self.db.execute(
            select(PlatformAdmin).where(PlatformAdmin.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> PlatformAdmin | None:
        result = await self.db.execute(
            select(PlatformAdmin).where(PlatformAdmin.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_reset_token(self, token_hash: str) -> PlatformAdmin | None:
        result = await self.db.execute(
            select(PlatformAdmin).where(
                PlatformAdmin.password_reset_token == token_hash
            )
        )
        return result.scalar_one_or_none()

    async def exists_any(self) -> bool:
        """Return True if at least one platform admin exists. Used by bootstrap."""
        result = await self.db.execute(select(PlatformAdmin).limit(1))
        return result.scalar_one_or_none() is not None

    async def list(self, skip: int = 0, limit: int = 50) -> list[PlatformAdmin]:
        result = await self.db.execute(
            select(PlatformAdmin)
            .order_by(PlatformAdmin.created_at)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(
        self,
        email: str,
        full_name: str,
        password_hash: str,
        is_super: bool = False,
        role: str = "manager",
    ) -> PlatformAdmin:
        admin = PlatformAdmin(
            id=uuid4(),
            email=email,
            full_name=full_name,
            password_hash=password_hash,
            is_super=is_super,
            role=role,
        )
        self.db.add(admin)
        await self.db.flush()
        await self.db.refresh(admin)
        return admin

    async def update(self, id: UUID, **fields) -> PlatformAdmin | None:
        admin = await self.get_by_id(id)
        if not admin:
            return None
        for key, value in fields.items():
            setattr(admin, key, value)
        await self.db.flush()
        await self.db.refresh(admin)
        return admin
