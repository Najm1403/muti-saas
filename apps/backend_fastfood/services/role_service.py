# services/role_service.py

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ConflictError, ForbiddenError, NotFoundError
from models.permission import Permission
from models.role import Role
from models.role_permission import RolePermission
from models.user_role import UserRole
from models.user import User
from models.user_permission import UserPermission
from schemas.permission import UserPermissionState
from schemas.role import RoleCreate, RoleResponse, RoleUpdate, PermissionResponse


class RoleService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list(self, tenant_id: UUID) -> list[RoleResponse]:
        result = await self.db.execute(
            select(Role)
            .where(Role.tenant_id == tenant_id, Role.deleted_at.is_(None))
            .order_by(Role.name)
        )
        return [RoleResponse.model_validate(r) for r in result.scalars().all()]

    async def create(self, tenant_id: UUID, data: RoleCreate) -> RoleResponse:
        # Uniqueness check within tenant
        existing = await self.db.execute(
            select(Role).where(
                Role.tenant_id == tenant_id,
                Role.name == data.name,
                Role.deleted_at.is_(None),
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictError(f"Role '{data.name}' already exists in this tenant.")

        role = Role(
            id=uuid4(),
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            is_active=True,
        )
        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)
        return RoleResponse.model_validate(role)

    async def get(self, id: UUID, tenant_id: UUID) -> RoleResponse:
        result = await self.db.execute(
            select(Role).where(Role.id == id, Role.tenant_id == tenant_id, Role.deleted_at.is_(None))
        )
        role = result.scalar_one_or_none()
        if not role:
            raise NotFoundError("Role not found.")
        return RoleResponse.model_validate(role)

    async def _get_model(self, id: UUID, tenant_id: UUID) -> Role:
        result = await self.db.execute(
            select(Role).where(Role.id == id, Role.tenant_id == tenant_id, Role.deleted_at.is_(None))
        )
        role = result.scalar_one_or_none()
        if not role:
            raise NotFoundError("Role not found.")
        return role

    async def update(self, id: UUID, tenant_id: UUID, data: RoleUpdate) -> RoleResponse:
        role = await self._get_model(id, tenant_id)
        if (role.name or '').strip().lower() in {'admin', 'owner'}:
            raise ForbiddenError('The tenant owner role is protected and cannot be edited.')
        if data.name is not None:
            # Name uniqueness check
            existing = await self.db.execute(
                select(Role).where(
                    Role.tenant_id == tenant_id,
                    Role.name == data.name,
                    Role.id != id,
                    Role.deleted_at.is_(None),
                )
            )
            if existing.scalar_one_or_none():
                raise ConflictError(f"Role '{data.name}' already exists.")
            role.name = data.name
        if data.description is not None:
            role.description = data.description
        if data.is_active is not None:
            role.is_active = data.is_active
        await self.db.commit()
        await self.db.refresh(role)
        return RoleResponse.model_validate(role)

    async def delete(self, id: UUID, tenant_id: UUID) -> None:
        from datetime import datetime, timezone
        role = await self._get_model(id, tenant_id)
        if (role.name or '').strip().lower() in {'admin', 'owner'}:
            raise ForbiddenError('The tenant owner role is protected and cannot be deleted.')
        role.deleted_at = datetime.now(timezone.utc)
        await self.db.commit()

    # ── Permissions ──────────────────────────────────────────────

    async def list_permissions(self) -> list[PermissionResponse]:
        """All system-level permissions (global, not tenant-scoped)."""
        result = await self.db.execute(
            select(Permission)
            .where(Permission.deleted_at.is_(None), Permission.is_active.is_(True))
            .order_by(Permission.module, Permission.code)
        )
        return [PermissionResponse.model_validate(p) for p in result.scalars().all()]

    async def list_role_permissions(self, role_id: UUID, tenant_id: UUID) -> list[PermissionResponse]:
        await self._get_model(role_id, tenant_id)
        result = await self.db.execute(
            select(Permission)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .where(
                RolePermission.role_id == role_id,
                RolePermission.deleted_at.is_(None),
                Permission.deleted_at.is_(None),
            )
            .order_by(Permission.module, Permission.code)
        )
        return [PermissionResponse.model_validate(p) for p in result.scalars().all()]

    async def assign_permission(self, role_id: UUID, permission_id: UUID, tenant_id: UUID) -> None:
        role = await self._get_model(role_id, tenant_id)
        if (role.name or '').strip().lower() in {'admin', 'owner'}:
            raise ForbiddenError('The tenant owner role always has full access and cannot be edited.')
        # Check permission exists
        perm = await self.db.execute(select(Permission).where(Permission.id == permission_id, Permission.deleted_at.is_(None)))
        if not perm.scalar_one_or_none():
            raise NotFoundError("Permission not found.")
        # Check not already assigned
        existing = await self.db.execute(
            select(RolePermission).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id,
            )
        )
        previous = existing.scalar_one_or_none()
        if previous:
            if previous.deleted_at is not None:
                previous.deleted_at = None
                await self.db.commit()
            return  # idempotent or restored
        rp = RolePermission(id=uuid4(), role_id=role_id, permission_id=permission_id)
        self.db.add(rp)
        await self.db.commit()

    async def remove_permission(self, role_id: UUID, permission_id: UUID, tenant_id: UUID) -> None:
        from datetime import datetime, timezone
        role = await self._get_model(role_id, tenant_id)
        if (role.name or '').strip().lower() in {'admin', 'owner'}:
            raise ForbiddenError('The tenant owner role always has full access and cannot be edited.')
        result = await self.db.execute(
            select(RolePermission).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id,
                RolePermission.deleted_at.is_(None),
            )
        )
        rp = result.scalar_one_or_none()
        if rp:
            rp.deleted_at = datetime.now(timezone.utc)
            await self.db.commit()

    # ── User-Role assignment ─────────────────────────────────────

    async def _check_user(self, user_id: UUID, tenant_id: UUID) -> None:
        if await self.db.scalar(select(User.id).where(User.id == user_id, User.tenant_id == tenant_id, User.deleted_at.is_(None))) is None:
            raise NotFoundError("User not found.")

    async def list_user_roles(self, user_id: UUID, tenant_id: UUID) -> list[RoleResponse]:
        await self._check_user(user_id, tenant_id)
        result = await self.db.execute(
            select(Role)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(
                UserRole.user_id == user_id,
                UserRole.deleted_at.is_(None),
                Role.tenant_id == tenant_id,
                Role.deleted_at.is_(None),
            )
            .order_by(Role.name)
        )
        return [RoleResponse.model_validate(r) for r in result.scalars().all()]

    async def assign_user_role(self, user_id: UUID, role_id: UUID, tenant_id: UUID) -> None:
        await self._check_user(user_id, tenant_id)
        await self._get_model(role_id, tenant_id)
        existing = await self.db.execute(
            select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
            )
        )
        previous = existing.scalar_one_or_none()
        if previous:
            if previous.deleted_at is not None:
                previous.deleted_at = None
                await self.db.commit()
            return  # idempotent or restored
        ur = UserRole(id=uuid4(), user_id=user_id, role_id=role_id)
        self.db.add(ur)
        await self.db.commit()

    async def remove_user_role(self, user_id: UUID, role_id: UUID, tenant_id: UUID) -> None:
        await self._check_user(user_id, tenant_id)
        role = await self._get_model(role_id, tenant_id)
        if (role.name or '').strip().lower() in {'admin', 'owner'}:
            raise ForbiddenError('The tenant owner role cannot be removed from its owner.')
        from datetime import datetime, timezone
        result = await self.db.execute(
            select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
                UserRole.deleted_at.is_(None),
            )
        )
        ur = result.scalar_one_or_none()
        if ur:
            ur.deleted_at = datetime.now(timezone.utc)
            await self.db.commit()

    async def _user_role_context(
        self, user_id: UUID, tenant_id: UUID
    ) -> tuple[bool, set[UUID]]:
        """Return wildcard-role state and active role-inherited permission IDs."""
        await self._check_user(user_id, tenant_id)
        role_names = set((await self.db.scalars(
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                UserRole.user_id == user_id,
                UserRole.deleted_at.is_(None),
                Role.tenant_id == tenant_id,
                Role.deleted_at.is_(None),
                Role.is_active.is_(True),
            )
        )).all())
        # Reuses the single source of truth for which role names grant
        # blanket wildcard access — api.dependencies.get_user_permissions()
        # is what actually gates every request, so a locally duplicated
        # copy here could silently drift and show the wrong override state
        # on the permissions-editing screen.
        from api.dependencies import _ADMIN_ROLE_NAMES
        has_full_access = any(
            (name or "").strip().lower() in _ADMIN_ROLE_NAMES
            for name in role_names
        )
        inherited = set((await self.db.scalars(
            select(Permission.id)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                UserRole.user_id == user_id,
                UserRole.deleted_at.is_(None),
                RolePermission.deleted_at.is_(None),
                Role.tenant_id == tenant_id,
                Role.deleted_at.is_(None),
                Role.is_active.is_(True),
                Permission.deleted_at.is_(None),
                Permission.is_active.is_(True),
            )
        )).all())
        return has_full_access, inherited

    async def list_user_permissions(
        self, user_id: UUID, tenant_id: UUID
    ) -> list[UserPermissionState]:
        """List every active permission with the user's effective checkbox state."""
        has_full_access, inherited = await self._user_role_context(user_id, tenant_id)
        permissions = (await self.db.scalars(
            select(Permission)
            .where(Permission.deleted_at.is_(None), Permission.is_active.is_(True))
            .order_by(Permission.module, Permission.code)
        )).all()
        overrides = {
            permission_id: is_allowed
            for permission_id, is_allowed in (await self.db.execute(
                select(UserPermission.permission_id, UserPermission.is_allowed)
                .where(
                    UserPermission.user_id == user_id,
                    UserPermission.deleted_at.is_(None),
                )
            )).all()
        }
        result = []
        for permission in permissions:
            inherited_value = has_full_access or permission.id in inherited
            checked = overrides.get(permission.id, inherited_value)
            result.append(UserPermissionState(
                id=permission.id,
                code=permission.code,
                name=permission.name,
                description=permission.description,
                module=permission.module,
                checked=checked,
                inherited=inherited_value,
                overridden=permission.id in overrides,
            ))
        return result

    async def replace_user_permissions(
        self, user_id: UUID, tenant_id: UUID, permission_ids: list[UUID]
    ) -> list[UserPermissionState]:
        """Replace one user's effective permissions without changing shared roles."""
        has_full_access, inherited = await self._user_role_context(user_id, tenant_id)
        if has_full_access:
            raise ForbiddenError(
                "This user's Admin/Owner/Manager role already grants full access. "
                "Change that role assignment before setting individual permissions."
            )
        selected = set(permission_ids)
        valid = set((await self.db.scalars(
            select(Permission.id).where(
                Permission.id.in_(selected),
                Permission.deleted_at.is_(None),
                Permission.is_active.is_(True),
            )
        )).all()) if selected else set()
        if valid != selected:
            raise NotFoundError("One or more permissions are invalid or inactive.")

        await self.db.execute(delete(UserPermission).where(UserPermission.user_id == user_id))
        for permission_id in sorted(selected - inherited, key=str):
            self.db.add(UserPermission(
                id=uuid4(), user_id=user_id, permission_id=permission_id, is_allowed=True
            ))
        for permission_id in sorted(inherited - selected, key=str):
            self.db.add(UserPermission(
                id=uuid4(), user_id=user_id, permission_id=permission_id, is_allowed=False
            ))
        await self.db.commit()
        return await self.list_user_permissions(user_id, tenant_id)
