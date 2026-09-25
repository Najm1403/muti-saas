from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from models.user_role import UserRole


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, id: UUID, tenant_id: UUID) -> User | None:
        stmt = select(User).where(
            User.id == id,
            User.tenant_id == tenant_id,
            User.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str, tenant_id: UUID) -> User | None:
        stmt = select(User).where(
            User.username == username,
            User.tenant_id == tenant_id,
            User.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str, tenant_id: UUID) -> User | None:
        """Look up an active user by email within a tenant. Used by forgot-password flow."""
        stmt = select(User).where(
            User.email == email,
            User.tenant_id == tenant_id,
            User.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_reset_token(self, token_hash: str, tenant_id: UUID) -> User | None:
        """Look up a user by their hashed reset token within a tenant."""
        stmt = select(User).where(
            User.password_reset_token == token_hash,
            User.tenant_id == tenant_id,
            User.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, tenant_id: UUID, skip: int = 0, limit: int = 50) -> list[User]:
        stmt = (
            select(User)
            .where(User.tenant_id == tenant_id, User.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        tenant_id: UUID,
        username: str,
        full_name: str,
        password_hash: str,
        email: str | None = None,
        pin_hash: str | None = None,
        photo_url: str | None = None,
        max_discount_percent: Decimal | None = None,
    ) -> User:
        existing = await self.get_by_username(username, tenant_id)
        if existing:
            raise ValueError(f"Username '{username}' already exists in tenant '{tenant_id}'.")
        user = User(
            id=uuid4(),
            tenant_id=tenant_id,
            username=username,
            full_name=full_name,
            password_hash=password_hash,
            email=email,
            pin_hash=pin_hash,
            photo_url=photo_url,
            max_discount_percent=max_discount_percent,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update(self, id: UUID, tenant_id: UUID, **fields) -> User | None:
        user = await self.get_by_id(id, tenant_id)
        if not user:
            return None
        for key, value in fields.items():
            setattr(user, key, value)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def soft_delete(self, id: UUID, tenant_id: UUID) -> bool:
        user = await self.get_by_id(id, tenant_id)
        if not user:
            return False
        user.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True

    async def assign_role(self, user_id: UUID, role_id: UUID) -> UserRole:
        stmt = select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
            UserRole.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            return existing
        user_role = UserRole(id=uuid4(), user_id=user_id, role_id=role_id)
        self.db.add(user_role)
        await self.db.flush()
        await self.db.refresh(user_role)
        return user_role

    async def remove_role(self, user_id: UUID, role_id: UUID) -> bool:
        stmt = select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
            UserRole.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        user_role = result.scalar_one_or_none()
        if not user_role:
            return False
        user_role.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True
