# services/tenant_service.py

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ConflictError, NotFoundError
from models.branch import Branch
from models.business import Business
from models.category import Category
from models.device import Device
from models.product import Product
from models.user import User
from repositories.tenant_repository import TenantRepository
from schemas.tenant import TenantCreate, TenantResponse, TenantUpdate
from schemas.common import MessageResponse


class TenantService:
    """
    Orchestrates all tenant lifecycle operations.

    Tenant is the root of the multi-tenant hierarchy:
        Tenant → Business → Branch → Device → User → Sale

    Only a super-admin should be able to call these endpoints.
    Authorization enforcement belongs in the route layer.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = TenantRepository(db)

    async def create(self, data: TenantCreate) -> TenantResponse:
        try:
            tenant = await self.repo.create(
                name=data.name,
                tenant_code=data.tenant_code,
                business_template_id=data.business_template_id,
            )
            await self.db.commit()
            await self.db.refresh(tenant)
            return TenantResponse.model_validate(tenant)
        except ValueError as exc:
            await self.db.rollback()
            raise ConflictError(str(exc)) from exc

    async def get(self, id: UUID) -> TenantResponse:
        tenant = await self.repo.get_by_id(id)
        if not tenant:
            raise NotFoundError("Tenant not found.")
        return TenantResponse.model_validate(tenant)

    async def get_by_code(self, tenant_code: str) -> TenantResponse:
        tenant = await self.repo.get_by_code(tenant_code)
        if not tenant:
            raise NotFoundError("Tenant not found.")
        return TenantResponse.model_validate(tenant)

    async def list(self, skip: int = 0, limit: int = 50) -> list[TenantResponse]:
        tenants = await self.repo.list(skip=skip, limit=limit)
        return [TenantResponse.model_validate(t) for t in tenants]

    async def update(self, id: UUID, data: TenantUpdate) -> TenantResponse:
        tenant = await self.repo.get_by_id(id)
        if not tenant:
            raise NotFoundError("Tenant not found.")

        fields = data.model_dump(exclude_none=True)
        if not fields:
            return TenantResponse.model_validate(tenant)

        tenant = await self.repo.update(id, **fields)
        await self.db.commit()
        await self.db.refresh(tenant)
        return TenantResponse.model_validate(tenant)

    async def set_admin_message(self, id: UUID, message: str) -> TenantResponse:
        """Set (or replace) the notice shown to the tenant on dashboard login.

        A separate action from the generic update() PATCH so clearing it
        (see clear_admin_message) can unambiguously mean "remove the
        message," which update()'s exclude_none semantics can't express —
        passing admin_message=None through update() would just be ignored,
        not applied.
        """
        tenant = await self.repo.get_by_id(id)
        if not tenant:
            raise NotFoundError("Tenant not found.")
        tenant = await self.repo.update(
            id, admin_message=message, admin_message_set_at=datetime.now(timezone.utc),
        )
        await self.db.commit()
        await self.db.refresh(tenant)
        return TenantResponse.model_validate(tenant)

    async def clear_admin_message(self, id: UUID) -> TenantResponse:
        tenant = await self.repo.get_by_id(id)
        if not tenant:
            raise NotFoundError("Tenant not found.")
        tenant = await self.repo.update(id, admin_message=None, admin_message_set_at=None)
        await self.db.commit()
        await self.db.refresh(tenant)
        return TenantResponse.model_validate(tenant)

    async def activate(self, id: UUID) -> TenantResponse:
        tenant = await self.repo.set_active(id, is_active=True)
        if not tenant:
            raise NotFoundError("Tenant not found.")
        await self.db.commit()
        await self.db.refresh(tenant)
        return TenantResponse.model_validate(tenant)

    async def deactivate(self, id: UUID) -> TenantResponse:
        tenant = await self.repo.set_active(id, is_active=False)
        if not tenant:
            raise NotFoundError("Tenant not found.")
        await self.db.commit()
        await self.db.refresh(tenant)
        return TenantResponse.model_validate(tenant)

    async def delete(self, id: UUID) -> MessageResponse:
        deleted = await self.repo.soft_delete(id)
        if not deleted:
            raise NotFoundError("Tenant not found.")
        await self._cascade_soft_delete(id)
        await self.db.commit()
        return MessageResponse(message="Tenant deleted successfully.")

    async def _cascade_soft_delete(self, tenant_id: UUID) -> None:
        """
        Soft-deleting only the Tenant row leaves its Business/Branch/Device/
        Category/Product/User rows "live" — every one of those tables is
        normally queried by filtering its own deleted_at, without joining
        back to Tenant, so a deleted tenant's leftover rows would still be
        fetchable (this is what previously inflated the platform dashboard's
        aggregate counts). Cascade the soft-delete down so that can't happen.
        """
        now = datetime.now(timezone.utc)

        await self.db.execute(
            update(Business).where(Business.tenant_id == tenant_id, Business.deleted_at.is_(None))
            .values(deleted_at=now)
        )
        await self.db.execute(
            update(User).where(User.tenant_id == tenant_id, User.deleted_at.is_(None))
            .values(deleted_at=now)
        )

        biz_ids = (await self.db.execute(
            select(Business.id).where(Business.tenant_id == tenant_id)
        )).scalars().all()
        if not biz_ids:
            return

        branch_ids = (await self.db.execute(
            select(Branch.id).where(Branch.business_id.in_(biz_ids))
        )).scalars().all()
        await self.db.execute(
            update(Branch).where(Branch.business_id.in_(biz_ids), Branch.deleted_at.is_(None))
            .values(deleted_at=now)
        )
        if branch_ids:
            await self.db.execute(
                update(Device).where(Device.branch_id.in_(branch_ids), Device.deleted_at.is_(None))
                .values(deleted_at=now)
            )

        cat_ids = (await self.db.execute(
            select(Category.id).where(Category.business_id.in_(biz_ids))
        )).scalars().all()
        await self.db.execute(
            update(Category).where(Category.business_id.in_(biz_ids), Category.deleted_at.is_(None))
            .values(deleted_at=now)
        )
        if cat_ids:
            await self.db.execute(
                update(Product).where(Product.category_id.in_(cat_ids), Product.deleted_at.is_(None))
                .values(deleted_at=now)
            )
