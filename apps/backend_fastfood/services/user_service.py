# services/user_service.py
#
# Manages users within a tenant.
#
# Hierarchy this service enforces:
#   Tenant → User
#
# Dependencies:
#   - repositories/user_repository.py  — all DB operations for User rows
#   - core/security.py                 — hash_password, verify_password
#   - schemas/user.py                  — UserCreate, UserUpdate, UserResponse
#   - core/exceptions.py               — ConflictError, NotFoundError, AuthenticationError

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import AuthenticationError, ConflictError, ForbiddenError, NotFoundError, ValidationError
from core.security import hash_password, verify_password
from models.branch import Branch
from models.business import Business
from models.employee import Employee
from models.user_branch import UserBranch
from models.user_role import UserRole
from models.role import Role
from repositories.user_repository import UserRepository
from schemas.branch_assignment import BranchAssignmentResponse, BranchBrief
from schemas.user import UserCreate, UserResponse, UserUpdate


class UserService:
    """
    Manages tenant user accounts: creation, profile updates, activation, and deletion.

    Users belong to exactly one Tenant.  The tenant_id from the JWT is passed
    to every method so that a user can only see and modify accounts within
    their own tenant.

    Password handling:
        - Passwords are accepted as plain text in UserCreate.
        - This service hashes them with bcrypt before storage.
        - The raw password is never persisted.

    Username uniqueness:
        - Usernames are unique within a tenant (enforced by DB constraint
          uq_user_tenant_username and checked in the repository before INSERT).
        - Two tenants may independently have a user named "admin".
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = UserRepository(db)

    async def _is_protected_owner(self, user_id: UUID, tenant_id: UUID) -> bool:
        """The onboarding owner is the user holding the protected Admin role."""
        return bool(await self.db.scalar(
            select(UserRole.user_id)
            .join(Role, Role.id == UserRole.role_id)
            .where(
                UserRole.user_id == user_id,
                Role.tenant_id == tenant_id,
                Role.name.ilike('admin'),
                UserRole.deleted_at.is_(None),
                Role.deleted_at.is_(None),
            )
        ))

    # ── public interface ─────────────────────────────────────────────────

    async def create(self, tenant_id: UUID, data: UserCreate) -> UserResponse:
        """
        Create a new user by promoting an existing, active Employee.

        full_name is always taken from the Employee record — a User never
        carries its own, separately-typed name — so the login and the HR
        record can never drift apart. Hashes the plain-text password before
        storing. Raises NotFoundError if the employee doesn't exist (or
        isn't active), ValidationError if it's already linked to another
        User, ConflictError if the username is already taken within this
        tenant.
        """
        employee = await self.db.scalar(
            select(Employee).where(
                Employee.id == data.employee_id,
                Employee.tenant_id == tenant_id,
                Employee.deleted_at.is_(None),
            )
        )
        if not employee:
            raise NotFoundError("Employee not found.")
        if employee.status != "active":
            raise ValidationError("Only active employees can be made a user.")
        if employee.user_id is not None:
            raise ValidationError("This employee is already linked to a user account.")

        try:
            user = await self.repo.create(
                tenant_id=tenant_id,
                username=data.username,
                full_name=employee.full_name,
                password_hash=hash_password(data.password),
                email=str(data.email) if data.email else None,
                pin_hash=hash_password(data.pin) if data.pin else None,
                photo_url=data.photo_url,
                max_discount_percent=data.max_discount_percent,
            )
        except ValueError as exc:
            raise ConflictError(str(exc)) from exc
        employee.user_id = user.id
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise ValidationError("This employee is already linked to a user account.")
        return UserResponse.model_validate(user)

    async def get(self, id: UUID, tenant_id: UUID) -> UserResponse:
        """
        Return a single user by UUID, scoped to the tenant.

        Raises NotFoundError if the user does not exist or belongs to a
        different tenant.
        """
        user = await self.repo.get_by_id(id, tenant_id)
        if not user:
            raise NotFoundError("User not found.")
        return UserResponse.model_validate(user)

    async def list(
        self, tenant_id: UUID, skip: int = 0, limit: int = 50
    ) -> list[UserResponse]:
        """
        Return all active users within the tenant, with pagination.

        Deleted users (soft-deleted) are excluded automatically by the
        repository query.
        """
        users = await self.repo.list(tenant_id=tenant_id, skip=skip, limit=limit)
        return [UserResponse.model_validate(u) for u in users]

    async def update(
        self, id: UUID, tenant_id: UUID, data: UserUpdate
    ) -> UserResponse:
        """
        Partially update a user's profile fields.

        Handles username rename: checks uniqueness within the tenant before
        persisting so the DB constraint is never hit as a raw IntegrityError.
        Only fields present in the request body are changed (exclude_unset).
        """
        if not await self.repo.get_by_id(id, tenant_id):
            raise NotFoundError("User not found.")
        if await self._is_protected_owner(id, tenant_id):
            raise ForbiddenError("The tenant owner account is protected and cannot be edited.")

        fields = data.model_dump(exclude_unset=True)

        if "username" in fields:
            existing = await self.repo.get_by_username(fields["username"], tenant_id)
            if existing and existing.id != id:
                raise ConflictError(
                    f"Username '{fields['username']}' is already taken within this tenant."
                )

        user = await self.repo.update(id, tenant_id, **fields)
        await self.db.commit()
        return UserResponse.model_validate(user)

    async def activate(self, id: UUID, tenant_id: UUID) -> UserResponse:
        """Re-enable a previously deactivated user account."""
        if not await self.repo.get_by_id(id, tenant_id):
            raise NotFoundError("User not found.")
        user = await self.repo.update(id, tenant_id, is_active=True)
        await self.db.commit()
        return UserResponse.model_validate(user)

    async def deactivate(self, id: UUID, tenant_id: UUID) -> UserResponse:
        """
        Disable a user account (is_active = False).

        The account is not deleted — the user can be reactivated later.
        A deactivated user cannot log in (auth service checks is_active).
        """
        if not await self.repo.get_by_id(id, tenant_id):
            raise NotFoundError("User not found.")
        if await self._is_protected_owner(id, tenant_id):
            raise ForbiddenError("The tenant owner account cannot be deactivated.")
        user = await self.repo.update(id, tenant_id, is_active=False)
        await self.db.commit()
        return UserResponse.model_validate(user)

    async def change_password(
        self,
        id: UUID,
        tenant_id: UUID,
        current_password: str,
        new_password: str,
    ) -> None:
        """
        Change a user's password after verifying the current one.

        Steps:
            1. Load the user (raises NotFoundError if missing).
            2. Verify current_password against the stored hash.
            3. Hash new_password and persist it.

        Raises AuthenticationError if current_password does not match.
        This prevents a stolen session from silently changing a password.
        """
        user = await self.repo.get_by_id(id, tenant_id)
        if not user:
            raise NotFoundError("User not found.")
        if not verify_password(current_password, user.password_hash):
            raise AuthenticationError("Current password is incorrect.")
        await self.repo.update(id, tenant_id, password_hash=hash_password(new_password))
        await self.db.commit()

    async def admin_reset_password(
        self, id: UUID, tenant_id: UUID, new_password: str
    ) -> None:
        """
        Force-set a user's password without requiring the current password.

        Intended for tenant admins who need to reset a forgotten or compromised
        password on behalf of a user. The user's existing sessions remain valid
        until they expire (no active session invalidation in V1).
        """
        user = await self.repo.get_by_id(id, tenant_id)
        if not user:
            raise NotFoundError("User not found.")
        await self.repo.update(id, tenant_id, password_hash=hash_password(new_password))
        await self.db.commit()

    async def set_pin(self, id: UUID, tenant_id: UUID, pin: str) -> UserResponse:
        """Set or replace a user's POS quick sign-in PIN (admin action).

        The tenant owner/admin may also hold a PIN and act as a cashier —
        unlike update()/deactivate()/set_branch_assignment(), this is not one
        of the protections that would lock the owner out of their own tenant,
        so it deliberately does not check _is_protected_owner().
        """
        user = await self.repo.get_by_id(id, tenant_id)
        if not user:
            raise NotFoundError("User not found.")
        user = await self.repo.update(id, tenant_id, pin_hash=hash_password(pin))
        await self.db.commit()
        return UserResponse.model_validate(user)

    async def delete(self, id: UUID, tenant_id: UUID) -> None:
        """
        Soft-delete a user account (sets deleted_at).

        The user's historical sales records are preserved.  Login attempts
        by a soft-deleted user will fail because the auth query filters
        deleted_at.is_(None).
        """
        if await self._is_protected_owner(id, tenant_id):
            raise ForbiddenError("The tenant owner account cannot be deleted.")
        if not await self.repo.soft_delete(id, tenant_id):
            raise NotFoundError("User not found.")
        await self.db.commit()

    # ── Branch assignment ────────────────────────────────────────────────

    async def get_branch_assignment(
        self, user_id: UUID, tenant_id: UUID
    ) -> BranchAssignmentResponse:
        user = await self.repo.get_by_id(user_id, tenant_id)
        if not user:
            raise NotFoundError("User not found.")
        if user.all_branches:
            return BranchAssignmentResponse(all_branches=True, branches=[])
        result = await self.db.execute(
            select(Branch)
            .join(UserBranch, UserBranch.branch_id == Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .where(Business.tenant_id == tenant_id, UserBranch.user_id == user_id)
            .where(Branch.deleted_at.is_(None))
            .order_by(Branch.name)
        )
        branches = result.scalars().all()
        return BranchAssignmentResponse(
            all_branches=False,
            branches=[BranchBrief(id=b.id, name=b.name, branch_code=b.branch_code) for b in branches],
        )

    async def set_branch_assignment(
        self, user_id: UUID, tenant_id: UUID, all_branches: bool, branch_ids: list[UUID]
    ) -> BranchAssignmentResponse:
        user = await self.repo.get_by_id(user_id, tenant_id)
        if not user:
            raise NotFoundError("User not found.")
        if await self._is_protected_owner(user_id, tenant_id):
            raise ForbiddenError("The tenant owner has access to every branch and cannot be reassigned.")
        branch_ids = list(dict.fromkeys(branch_ids))
        if branch_ids:
            owned = (await self.db.scalars(select(Branch.id).join(Business, Branch.business_id == Business.id).where(
                Branch.id.in_(branch_ids), Business.tenant_id == tenant_id,
                Business.deleted_at.is_(None), Branch.deleted_at.is_(None),
            ))).all()
            if set(owned) != set(branch_ids):
                raise NotFoundError("Branch not found in this tenant.")
        user.all_branches = all_branches
        await self.db.execute(
            delete(UserBranch).where(UserBranch.user_id == user_id)
        )
        assigned: list[Branch] = []
        if not all_branches and branch_ids:
            for bid in branch_ids:
                self.db.add(UserBranch(user_id=user_id, branch_id=bid))
            await self.db.flush()
            result = await self.db.execute(
                select(Branch)
                .where(Branch.id.in_(branch_ids))
                .where(Branch.deleted_at.is_(None))
                .order_by(Branch.name)
            )
            assigned = list(result.scalars().all())
        await self.db.commit()
        return BranchAssignmentResponse(
            all_branches=all_branches,
            branches=[BranchBrief(id=b.id, name=b.name, branch_code=b.branch_code) for b in assigned],
        )
