# services/onboarding_service.py
#
# Platform-level tenant onboarding and management service.
#
# Methods
# -------
# onboard(data)           — Creates Tenant + Owner + Admin Role + Business +
#                           Branch + Subscription in a single DB transaction,
#                           then seeds Categories / Variant Option Groups /
#                           Add-on Groups from the chosen BusinessTemplate.
#                           One COMMIT or full rollback — nothing partial lands.
#
# get_tenant_detail(id)   — Enriched tenant view for the platform admin UI.
#                           Queries user/branch/device counts directly (cross-
#                           tenant DB access is allowed for platform admins).
#
# list_tenant_branches(id) — All branches for a tenant, with user + device counts.
#
# create_tenant_branch(id, data) — Creates a branch for a tenant's Business
#                                  from the platform admin UI.
#
# Depends on
# ----------
#   models:       Tenant, User, Role, UserRole, Business, Branch, Subscription,
#                 BusinessTemplate, Category, VariantOptionGroup, VariantOption,
#                 AddonGroup, AddonItem
#   repositories: TenantRepository, BusinessRepository, PlanRepository,
#                 SubscriptionRepository
#   core:         hash_password (core.security)
#   exceptions:   ConflictError, NotFoundError, ValidationError (core.exceptions)

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ConflictError, NotFoundError, ValidationError
from core.security import hash_password
from models.addon_group import AddonGroup
from models.addon_item import AddonItem
from models.audit_log import AuditLog
from models.branch import Branch
from models.business import Business
from models.business_template import BusinessTemplate
from models.category import Category
from models.device import Device
from models.role import Role
from models.subscription import BillingCycle, Subscription, SubscriptionStatus
from models.tenant import Tenant
from models.user import User
from models.user_branch import UserBranch
from models.user_role import UserRole
from models.variant_option import VariantOption
from models.variant_option_group import VariantOptionGroup
from repositories.business_repository import BusinessRepository
from repositories.plan_repository import PlanRepository
from repositories.subscription_repository import SubscriptionRepository
from repositories.tenant_repository import TenantRepository
from schemas.onboarding import (
    ActivityLogResponse,
    BranchPlatformCreate,
    BranchPlatformResponse,
    BranchPlatformUpdate,
    DashboardStats,
    DeviceHealthResponse,
    DevicePlatformResponse,
    OnboardingCreate,
    OnboardingResponse,
    TenantDetailResponse,
    TenantUserCreate,
    TenantUserResponse,
)
from services.plan_quota_service import enforce_branch_creation_quota


class OnboardingService:
    """
    Orchestrates platform-level tenant lifecycle operations.

    All write operations run inside a single SQLAlchemy session.
    Repositories FLUSH (never commit) — this service issues the
    single COMMIT at the end of each successful transaction.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ================================================================
    # ONBOARD — single atomic transaction
    # ================================================================

    async def onboard(self, data: OnboardingCreate) -> OnboardingResponse:
        """
        Create a complete tenant setup in one transaction:

            Tenant (business_template_id)
              └── Owner User  ← auto-generated temp password (hashed)
                    └── Admin Role assignment
              └── Business    ← same name as tenant
                    └── Initial Branch
              └── Subscription  ← only if plan_id provided

        Then seeds Categories / Variant Option Groups / Add-on Groups from
        the chosen BusinessTemplate's config (spec Part C / D5).

        Raises ConflictError  if tenant_code is already taken.
        Raises NotFoundError  if plan_id or business_template_id does not exist.
        Raises ValidationError on unexpected DB failures.
        """

        # ── Pre-flight uniqueness / existence checks ────────────────────────
        # Do all reads BEFORE any writes so domain errors are clean.

        tenant_repo = TenantRepository(self.db)
        if await tenant_repo.get_by_code(data.tenant_code):
            raise ConflictError(
                f"Tenant code '{data.tenant_code}' is already in use."
            )

        template = await self.db.scalar(
            select(BusinessTemplate).where(BusinessTemplate.id == data.business_template_id)
        )
        if not template:
            raise NotFoundError(f"Business template '{data.business_template_id}' not found.")

        plan = None
        if data.plan_id:
            plan = await PlanRepository(self.db).get_by_id(data.plan_id)
            if not plan:
                raise NotFoundError(f"Plan '{data.plan_id}' not found.")

        try:
            # ── 1. Tenant ───────────────────────────────────────────────────
            tenant = Tenant(
                id=uuid4(),
                name=data.name,
                tenant_code=data.tenant_code,
                is_active=True,
                business_template_id=template.id,
            )
            self.db.add(tenant)
            await self.db.flush()   # get tenant.id without committing

            # ── 2. Owner User ───────────────────────────────────────────────
            # Temporary password — random 16-char URL-safe token.
            # Never returned to the caller; owner sets their own via Account Recovery.
            temp_password = secrets.token_urlsafe(16)
            owner = User(
                id=uuid4(),
                tenant_id=tenant.id,
                username=data.owner_username,
                full_name=data.owner_name,
                email=data.owner_email,
                password_hash=hash_password(temp_password),
                is_active=True,
                all_branches=True,   # the shop owner can operate every branch
            )
            self.db.add(owner)
            await self.db.flush()

            # ── 3. Admin Role ────────────────────────────────────────────────
            # Create a tenant-scoped "Admin" role and assign it to the owner.
            # Role is tenant-scoped (Role.tenant_id = tenant.id) per the Role model.
            admin_role = Role(
                id=uuid4(),
                tenant_id=tenant.id,
                name="Admin",
                description="Tenant Administrator — full access to this tenant.",
                is_active=True,
            )
            self.db.add(admin_role)
            await self.db.flush()

            user_role = UserRole(
                id=uuid4(),
                user_id=owner.id,
                role_id=admin_role.id,
            )
            self.db.add(user_role)
            await self.db.flush()

            # ── 4. Business ──────────────────────────────────────────────────
            # A Tenant has exactly one Business (spec A2).
            inventory_config = (template.config or {}).get("inventory", {}) or {}
            business = Business(
                id=uuid4(),
                tenant_id=tenant.id,
                name=data.name,
                currency=data.currency,
                low_stock_threshold=max(0, int(inventory_config.get("low_stock_threshold", 5))),
                is_active=True,
            )
            self.db.add(business)
            await self.db.flush()

            # ── 5. Initial Branch ────────────────────────────────────────────
            branch = Branch(
                id=uuid4(),
                business_id=business.id,
                branch_code=data.branch_code,
                name=data.branch_name,
                is_active=True,
            )
            self.db.add(branch)
            await self.db.flush()

            # ── 6. Subscription ──────────────────────────────────────────────
            subscription: Subscription | None = None
            if plan:
                now = datetime.now(timezone.utc)
                if data.trial_days > 0:
                    trial_ends_at = now + timedelta(days=data.trial_days)
                    status       = SubscriptionStatus.TRIAL
                    # Expires 30 days after trial ends (platform can extend later)
                    expires_at   = trial_ends_at + timedelta(days=30)
                else:
                    trial_ends_at = None
                    status        = SubscriptionStatus.ACTIVE
                    expires_at    = now + timedelta(
                        days=365 if data.billing_cycle == BillingCycle.YEARLY else 30
                    )

                subscription = Subscription(
                    id=uuid4(),
                    tenant_id=tenant.id,
                    plan_id=plan.id,
                    billing_cycle=data.billing_cycle,
                    status=status,
                    started_at=now,
                    expires_at=expires_at,
                    trial_ends_at=trial_ends_at,
                )
                self.db.add(subscription)
                await self.db.flush()

            # ── 7. Seed from BusinessTemplate.config (spec Part C / D5) ──────
            config = template.config or {}

            for cat_name in config.get("categories", {}).get("default_categories", []):
                self.db.add(Category(business_id=business.id, name=cat_name))
            await self.db.flush()

            for group_def in config.get("variants", {}).get("seed_groups", []):
                group = VariantOptionGroup(business_id=business.id, name=group_def["name"])
                self.db.add(group)
                await self.db.flush()
                for value in group_def.get("values", []):
                    self.db.add(VariantOption(option_group_id=group.id, name=value))
            await self.db.flush()

            for addon_def in config.get("addons", {}).get("seed_groups", []):
                addon_group = AddonGroup(
                    business_id=business.id,
                    name=addon_def["name"],
                    selection_type=addon_def.get("selection_type", "multiple"),
                    min_select=addon_def.get("min_select", 0),
                    max_select=addon_def.get("max_select"),
                )
                self.db.add(addon_group)
                await self.db.flush()
                for item_def in addon_def.get("items", []):
                    self.db.add(AddonItem(
                        addon_group_id=addon_group.id,
                        name=item_def["name"],
                        price_delta=item_def.get("price_delta", 0),
                        default_selected=item_def.get("default_selected", False),
                    ))
            await self.db.flush()

            # ── 8. Single commit — all or nothing ────────────────────────────
            await self.db.commit()

        except IntegrityError as exc:
            await self.db.rollback()
            # Surface DB-level unique constraint violations as ConflictError
            raise ConflictError(
                "Onboarding failed due to a duplicate value. "
                "Check tenant code and owner username."
            ) from exc

        except (ConflictError, NotFoundError, ValidationError):
            await self.db.rollback()
            raise

        except Exception as exc:
            await self.db.rollback()
            raise ValidationError(
                f"Onboarding failed unexpectedly: {exc}"
            ) from exc

        return OnboardingResponse(
            tenant_id=tenant.id,
            tenant_name=tenant.name,
            tenant_code=tenant.tenant_code,
            user_id=owner.id,
            owner_name=owner.full_name,
            owner_username=owner.username,
            owner_email=owner.email or "",
            business_id=business.id,
            branch_id=branch.id,
            branch_name=branch.name,
            branch_code=branch.branch_code,
            subscription_id=subscription.id if subscription else None,
            plan_name=plan.name if plan else None,
            trial_days=data.trial_days if (subscription and data.trial_days > 0) else None,
            owner_temp_password=temp_password,
        )

    # ================================================================
    # TENANT DETAIL — enriched platform admin view
    # ================================================================

    async def get_tenant_detail(self, tenant_id: UUID) -> TenantDetailResponse:
        """
        Return enriched tenant information for the platform admin detail screen.

        Queries the DB directly for counts (users, branches, devices) using
        cross-tenant joins — this is intentional and safe because only
        platform admins (no tenant JWT) can reach this endpoint.
        """

        # ── Fetch tenant ────────────────────────────────────────────────────
        tenant = await TenantRepository(self.db).get_by_id(tenant_id)
        if not tenant:
            raise NotFoundError("Tenant not found.")

        business_template_name: str | None = await self.db.scalar(
            select(BusinessTemplate.name).where(BusinessTemplate.id == tenant.business_template_id)
        )

        # ── Owner — first active user created for this tenant ───────────────
        owner_result = await self.db.execute(
            select(User)
            .where(User.tenant_id == tenant_id, User.deleted_at.is_(None))
            .order_by(User.created_at)
            .limit(1)
        )
        owner = owner_result.scalar_one_or_none()

        # ── Aggregate counts ─────────────────────────────────────────────────

        user_count: int = await self.db.scalar(
            select(func.count(User.id)).where(
                User.tenant_id == tenant_id,
                User.deleted_at.is_(None),
            )
        ) or 0

        branch_count: int = await self.db.scalar(
            select(func.count(Branch.id))
            .join(Business, Branch.business_id == Business.id)
            .where(
                Business.tenant_id == tenant_id,
                Branch.deleted_at.is_(None),
                Business.deleted_at.is_(None),
            )
        ) or 0

        device_count: int = await self.db.scalar(
            select(func.count(Device.id))
            .join(Branch, Device.branch_id == Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .where(
                Business.tenant_id == tenant_id,
                Device.deleted_at.is_(None),
                Branch.deleted_at.is_(None),
                Business.deleted_at.is_(None),
            )
        ) or 0

        # ── Active subscription ──────────────────────────────────────────────
        subscription = await SubscriptionRepository(self.db).get_active_for_tenant(
            tenant_id
        )

        plan_name: str | None = None
        if subscription:
            plan = await PlanRepository(self.db).get_by_id(subscription.plan_id)
            plan_name = plan.name if plan else None

        return TenantDetailResponse(
            id=tenant.id,
            name=tenant.name,
            tenant_code=tenant.tenant_code,
            is_active=tenant.is_active,
            created_at=tenant.created_at,
            business_template_id=tenant.business_template_id,
            business_template_name=business_template_name,
            owner_name=owner.full_name if owner else None,
            owner_email=owner.email if owner else None,
            owner_username=owner.username if owner else None,
            user_count=user_count,
            branch_count=branch_count,
            device_count=device_count,
            subscription_id=subscription.id if subscription else None,
            subscription_status=subscription.status.value if subscription else None,
            plan_name=plan_name,
            trial_ends_at=subscription.trial_ends_at if subscription else None,
            expires_at=subscription.expires_at if subscription else None,
        )

    # ================================================================
    # TENANT BRANCHES — platform admin branch management
    # ================================================================

    async def list_tenant_branches(
        self, tenant_id: UUID
    ) -> list[BranchPlatformResponse]:
        """
        Return all branches for a tenant, with per-branch user and device counts.

        Branches are stored under the tenant's Business:
            Business.tenant_id → Branch.business_id → Device.branch_id
        """

        # Verify tenant exists
        tenant = await TenantRepository(self.db).get_by_id(tenant_id)
        if not tenant:
            raise NotFoundError("Tenant not found.")

        # Fetch all branches for this tenant via business join
        branch_result = await self.db.execute(
            select(Branch)
            .join(Business, Branch.business_id == Business.id)
            .where(
                Business.tenant_id == tenant_id,
                Branch.deleted_at.is_(None),
                Business.deleted_at.is_(None),
            )
            .order_by(Branch.created_at)
        )
        branches = list(branch_result.scalars().all())

        responses: list[BranchPlatformResponse] = []
        for br in branches:
            # Per-branch device count
            dev_count: int = await self.db.scalar(
                select(func.count(Device.id)).where(
                    Device.branch_id == br.id,
                    Device.deleted_at.is_(None),
                )
            ) or 0

            user_count = await self._branch_user_count(tenant_id, br.id)
            responses.append(
                BranchPlatformResponse(
                    id=br.id,
                    name=br.name,
                    branch_code=br.branch_code,
                    address=br.address,
                    phone=br.phone,
                    is_active=br.is_active,
                    business_id=br.business_id,
                    created_at=br.created_at,
                    user_count=user_count,
                    device_count=dev_count,
                )
            )

        return responses

    async def _branch_user_count(self, tenant_id: UUID, branch_id: UUID) -> int:
        return await self.db.scalar(
            select(func.count(func.distinct(User.id)))
            .outerjoin(UserBranch, UserBranch.user_id == User.id)
            .where(
                User.tenant_id == tenant_id,
                User.deleted_at.is_(None),
                User.is_active.is_(True),
                or_(User.all_branches.is_(True), UserBranch.branch_id == branch_id),
            )
        ) or 0

    async def create_tenant_branch(
        self, tenant_id: UUID, data: BranchPlatformCreate
    ) -> BranchPlatformResponse:
        """
        Create a branch for the given tenant from the platform admin UI.

        Uses the tenant's Business (created during onboarding).
        Raises NotFoundError  if the tenant or its business is missing.
        Raises ConflictError  if branch_code already exists in the business.
        """

        # Verify tenant
        tenant = await TenantRepository(self.db).get_by_id(tenant_id)
        if not tenant:
            raise NotFoundError("Tenant not found.")

        business = await BusinessRepository(self.db).get_by_tenant_id(tenant_id)
        if not business:
            raise NotFoundError(
                "No business found for this tenant. "
                "Ensure the tenant was created via the onboarding endpoint."
            )

        await enforce_branch_creation_quota(self.db, tenant_id)

        # Check branch_code uniqueness within the business
        existing = await self.db.execute(
            select(Branch).where(
                Branch.business_id == business.id,
                Branch.branch_code == data.branch_code,
                Branch.deleted_at.is_(None),
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictError(
                f"Branch code '{data.branch_code}' already exists in this tenant."
            )

        try:
            branch = Branch(
                id=uuid4(),
                business_id=business.id,
                branch_code=data.branch_code,
                name=data.name,
                address=data.address,
                phone=data.phone,
                is_active=data.is_active,
            )
            self.db.add(branch)
            await self.db.flush()
            await self.db.commit()
            await self.db.refresh(branch)

        except IntegrityError as exc:
            await self.db.rollback()
            raise ConflictError(
                f"Branch code '{data.branch_code}' already exists in this tenant."
            ) from exc

        return BranchPlatformResponse(
            id=branch.id,
            name=branch.name,
            branch_code=branch.branch_code,
            address=branch.address,
            phone=branch.phone,
            is_active=branch.is_active,
            business_id=branch.business_id,
            created_at=branch.created_at,
            user_count=await self._branch_user_count(tenant_id, branch.id),
            device_count=0,
        )

    # ================================================================
    # TENANT DEVICES — platform admin device management
    # ================================================================

    async def list_tenant_devices(
        self, tenant_id: UUID
    ) -> list[DevicePlatformResponse]:
        """
        Return all devices registered across all branches of a tenant.

        Joins Device → Branch → Business to scope by tenant_id.
        Returns branch name and branch_code alongside each device so the
        platform admin can see which branch each device belongs to.
        """

        tenant = await TenantRepository(self.db).get_by_id(tenant_id)
        if not tenant:
            raise NotFoundError("Tenant not found.")

        result = await self.db.execute(
            select(Device, Branch)
            .join(Branch, Device.branch_id == Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .where(
                Business.tenant_id == tenant_id,
                Device.deleted_at.is_(None),
                Branch.deleted_at.is_(None),
                Business.deleted_at.is_(None),
            )
            .order_by(Branch.name, Device.device_code)
        )
        rows = result.all()

        return [
            DevicePlatformResponse(
                id=device.id,
                branch_id=device.branch_id,
                branch_name=branch.name,
                branch_code=branch.branch_code,
                device_code=device.device_code,
                name=device.name,
                device_type=device.device_type,
                status=device.status.value,
                suspended_scope=device.suspended_scope.value if device.suspended_scope else None,
                is_active=device.is_active,
                is_activated=device.is_activated,
                last_sync_at=device.last_sync_at,
                activated_at=device.activated_at,
                created_at=device.created_at,
            )
            for device, branch in rows
        ]

    async def list_all_devices(self) -> list[DeviceHealthResponse]:
        """
        Return every device across all tenants.
        Joins Device → Branch → Business → Tenant.
        Used by the platform sync-health page.
        """
        result = await self.db.execute(
            select(Device, Branch, Tenant)
            .join(Branch, Device.branch_id == Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .join(Tenant, Business.tenant_id == Tenant.id)
            .where(
                Device.deleted_at.is_(None),
                Branch.deleted_at.is_(None),
                Business.deleted_at.is_(None),
                Tenant.deleted_at.is_(None),
            )
            .order_by(Tenant.name, Branch.name, Device.device_code)
        )
        rows = result.all()

        return [
            DeviceHealthResponse(
                id=device.id,
                branch_id=device.branch_id,
                branch_name=branch.name,
                branch_code=branch.branch_code,
                device_code=device.device_code,
                name=device.name,
                device_type=device.device_type,
                status=device.status.value,
                suspended_scope=device.suspended_scope.value if device.suspended_scope else None,
                is_active=device.is_active,
                is_activated=device.is_activated,
                last_sync_at=device.last_sync_at,
                activated_at=device.activated_at,
                created_at=device.created_at,
                tenant_id=tenant.id,
                tenant_name=tenant.name,
                tenant_code=tenant.tenant_code,
                contact=branch.phone,
            )
            for device, branch, tenant in rows
        ]

    # ================================================================
    # PLATFORM BRANCH UPDATE
    # ================================================================

    async def update_tenant_branch(
        self, tenant_id: UUID, branch_id: UUID, data: BranchPlatformUpdate
    ) -> BranchPlatformResponse:
        """
        Partial-update a branch that belongs to a given tenant.

        Only the fields present in ``data`` (non-None) are written.
        branch_code is intentionally not updatable to preserve device codes
        that were generated from it.
        """

        tenant = await TenantRepository(self.db).get_by_id(tenant_id)
        if not tenant:
            raise NotFoundError("Tenant not found.")

        branch_result = await self.db.execute(
            select(Branch)
            .join(Business, Branch.business_id == Business.id)
            .where(
                Branch.id == branch_id,
                Business.tenant_id == tenant_id,
                Branch.deleted_at.is_(None),
                Business.deleted_at.is_(None),
            )
        )
        branch = branch_result.scalar_one_or_none()
        if not branch:
            raise NotFoundError("Branch not found or does not belong to this tenant.")

        for field, value in data.model_dump(exclude_none=True).items():
            setattr(branch, field, value)

        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(branch)

        dev_count: int = await self.db.scalar(
            select(func.count(Device.id)).where(
                Device.branch_id == branch.id,
                Device.deleted_at.is_(None),
            )
        ) or 0

        return BranchPlatformResponse(
            id=branch.id,
            name=branch.name,
            branch_code=branch.branch_code,
            address=branch.address,
            phone=branch.phone,
            is_active=branch.is_active,
            business_id=branch.business_id,
            created_at=branch.created_at,
            user_count=await self._branch_user_count(tenant_id, branch.id),
            device_count=dev_count,
        )

    # ================================================================
    # TENANT USERS — platform admin view
    # ================================================================

    async def list_tenant_users(
        self, tenant_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[TenantUserResponse]:
        """
        Return all users belonging to a tenant, with their assigned role names.

        Uses cross-tenant DB access — platform admin only.
        """

        tenant = await TenantRepository(self.db).get_by_id(tenant_id)
        if not tenant:
            raise NotFoundError("Tenant not found.")

        user_result = await self.db.execute(
            select(User)
            .where(User.tenant_id == tenant_id, User.deleted_at.is_(None))
            .order_by(User.created_at)
            .offset(skip)
            .limit(limit)
        )
        users = list(user_result.scalars().all())

        responses: list[TenantUserResponse] = []
        for user in users:
            role_result = await self.db.execute(
                select(Role.name)
                .join(UserRole, Role.id == UserRole.role_id)
                .where(
                    UserRole.user_id == user.id,
                    UserRole.deleted_at.is_(None),
                    Role.deleted_at.is_(None),
                )
            )
            role_names = list(role_result.scalars().all())
            responses.append(
                TenantUserResponse(
                    id=user.id,
                    tenant_id=user.tenant_id,
                    username=user.username,
                    full_name=user.full_name,
                    email=user.email,
                    is_active=user.is_active,
                    created_at=user.created_at,
                    roles=role_names,
                )
            )

        return responses

    async def create_tenant_user(
        self, tenant_id: UUID, data: TenantUserCreate
    ) -> TenantUserResponse:
        """
        Create a new user inside a tenant from the platform admin UI.

        Optionally assigns the user to an existing role by name.
        If the named role does not exist, the user is created without a role.
        Raises ConflictError if username is already taken within the tenant.
        """

        tenant = await TenantRepository(self.db).get_by_id(tenant_id)
        if not tenant:
            raise NotFoundError("Tenant not found.")

        existing = await self.db.execute(
            select(User).where(
                User.tenant_id == tenant_id,
                User.username == data.username,
                User.deleted_at.is_(None),
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictError(
                f"Username '{data.username}' already exists in this tenant."
            )

        try:
            user = User(
                id=uuid4(),
                tenant_id=tenant_id,
                username=data.username,
                full_name=data.full_name,
                email=data.email,
                password_hash=hash_password(data.password),
                pin_hash=hash_password(data.pin) if data.pin else None,
                photo_url=data.photo_url,
                is_active=True,
            )
            self.db.add(user)
            await self.db.flush()

            # Assign role by name if it exists in this tenant
            role_result = await self.db.execute(
                select(Role).where(
                    Role.tenant_id == tenant_id,
                    Role.name == data.role_name,
                    Role.deleted_at.is_(None),
                )
            )
            role = role_result.scalar_one_or_none()

            role_names: list[str] = []
            if role:
                self.db.add(UserRole(id=uuid4(), user_id=user.id, role_id=role.id))
                await self.db.flush()
                role_names = [role.name]

            await self.db.commit()
            await self.db.refresh(user)

        except IntegrityError as exc:
            await self.db.rollback()
            raise ConflictError("Username already exists in this tenant.") from exc

        return TenantUserResponse(
            id=user.id,
            tenant_id=user.tenant_id,
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at,
            roles=role_names,
        )

    # ================================================================
    # DASHBOARD STATS
    # ================================================================

    async def get_dashboard_stats(self) -> DashboardStats:
        """
        Aggregate platform-wide stats for the super-admin dashboard.

        All counts exclude soft-deleted records.
        """

        total_tenants: int = await self.db.scalar(
            select(func.count(Tenant.id)).where(Tenant.deleted_at.is_(None))
        ) or 0

        active_tenants: int = await self.db.scalar(
            select(func.count(Tenant.id)).where(
                Tenant.deleted_at.is_(None),
                Tenant.is_active.is_(True),
            )
        ) or 0

        # Joined to Tenant (not just filtered by the child row's own deleted_at)
        # so a soft-deleted tenant's leftover users/branches/devices — which
        # tenant deletion does not cascade-delete — can never inflate these
        # platform-wide counts.
        total_users: int = await self.db.scalar(
            select(func.count(User.id)).join(Tenant, User.tenant_id == Tenant.id).where(
                User.deleted_at.is_(None), Tenant.deleted_at.is_(None),
            )
        ) or 0

        total_branches: int = await self.db.scalar(
            select(func.count(Branch.id))
            .join(Business, Branch.business_id == Business.id)
            .join(Tenant, Business.tenant_id == Tenant.id)
            .where(Branch.deleted_at.is_(None), Tenant.deleted_at.is_(None))
        ) or 0

        total_devices: int = await self.db.scalar(
            select(func.count(Device.id))
            .join(Branch, Device.branch_id == Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .join(Tenant, Business.tenant_id == Tenant.id)
            .where(Device.deleted_at.is_(None), Tenant.deleted_at.is_(None))
        ) or 0

        subscriptions_active: int = await self.db.scalar(
            select(func.count(Subscription.id))
            .join(Tenant, Subscription.tenant_id == Tenant.id)
            .where(Subscription.status == SubscriptionStatus.ACTIVE, Tenant.deleted_at.is_(None))
        ) or 0

        subscriptions_trial: int = await self.db.scalar(
            select(func.count(Subscription.id))
            .join(Tenant, Subscription.tenant_id == Tenant.id)
            .where(Subscription.status == SubscriptionStatus.TRIAL, Tenant.deleted_at.is_(None))
        ) or 0

        subscriptions_expired: int = await self.db.scalar(
            select(func.count(Subscription.id))
            .join(Tenant, Subscription.tenant_id == Tenant.id)
            .where(Subscription.status == SubscriptionStatus.EXPIRED, Tenant.deleted_at.is_(None))
        ) or 0

        return DashboardStats(
            total_tenants=total_tenants,
            active_tenants=active_tenants,
            suspended_tenants=total_tenants - active_tenants,
            trial_tenants=subscriptions_trial,
            total_users=total_users,
            total_branches=total_branches,
            total_devices=total_devices,
            subscriptions_active=subscriptions_active,
            subscriptions_trial=subscriptions_trial,
            subscriptions_expired=subscriptions_expired,
        )

    # ================================================================
    # ACTIVITY / AUDIT LOG
    # ================================================================

    async def list_activity(
        self,
        tenant_id: UUID | None = None,
        action: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ActivityLogResponse]:
        """
        Return audit log entries, newest first.

        Optionally scoped to a single tenant or filtered by action.
        Joins User and Tenant for display names — both outer joins because
        user_id can be null (system actions) and a tenant may be soft-deleted.
        """

        query = (
            select(AuditLog, User, Tenant)
            .outerjoin(User, AuditLog.user_id == User.id)
            .outerjoin(Tenant, AuditLog.tenant_id == Tenant.id)
            .where(AuditLog.deleted_at.is_(None))
        )
        if tenant_id:
            query = query.where(AuditLog.tenant_id == tenant_id)
        if action:
            query = query.where(AuditLog.action == action.upper())

        query = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        rows = result.all()

        return [
            ActivityLogResponse(
                id=log.id,
                tenant_id=log.tenant_id,
                tenant_name=tenant.name if tenant else None,
                user_id=log.user_id,
                username=user.username if user else None,
                action=log.action,
                module=log.module,
                entity_type=log.entity_type,
                entity_id=log.entity_id,
                description=log.description,
                ip_address=log.ip_address,
                created_at=log.created_at,
            )
            for log, user, tenant in rows
        ]
