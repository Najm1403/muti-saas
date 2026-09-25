# services/branch_service.py

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ConflictError, NotFoundError
from repositories.branch_repository import BranchRepository
from repositories.business_repository import BusinessRepository
from schemas.branch import BranchCreate, BranchResponse, BranchUpdate
from services.plan_quota_service import enforce_branch_creation_quota


class BranchService:
    """
    Manages branches under a business, scoped to a tenant.

    Hierarchy enforced:
        tenant_id → business_id → branch
    A branch can only be created under the business that belongs
    to the same tenant making the request.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = BranchRepository(db)
        self.business_repo = BusinessRepository(db)

    async def _verify_business(self, business_id: UUID, tenant_id: UUID) -> None:
        """Raise NotFoundError if the business doesn't belong to this tenant."""
        business = await self.business_repo.get_by_id(business_id, tenant_id)
        if not business:
            raise NotFoundError("Business not found.")

    async def create(
        self, business_id: UUID, tenant_id: UUID, data: BranchCreate
    ) -> BranchResponse:
        await self._verify_business(business_id, tenant_id)
        await enforce_branch_creation_quota(self.db, tenant_id)
        try:
            branch = await self.repo.create(
                business_id=business_id,
                tenant_id=tenant_id,
                branch_code=data.branch_code,
                name=data.name,
                address=data.address,
                phone=data.phone,
            )
        except ValueError as exc:
            raise ConflictError(str(exc)) from exc
        await self.db.commit()
        return BranchResponse.model_validate(branch)

    async def get(self, id: UUID, tenant_id: UUID) -> BranchResponse:
        branch = await self.repo.get_by_id(id, tenant_id)
        if not branch:
            raise NotFoundError("Branch not found.")
        return BranchResponse.model_validate(branch)

    async def list(
        self, business_id: UUID, tenant_id: UUID, skip: int = 0, limit: int = 50
    ) -> list[BranchResponse]:
        await self._verify_business(business_id, tenant_id)
        branches = await self.repo.list(
            business_id=business_id, tenant_id=tenant_id, skip=skip, limit=limit
        )
        return [BranchResponse.model_validate(b) for b in branches]

    async def update(
        self, id: UUID, tenant_id: UUID, data: BranchUpdate
    ) -> BranchResponse:
        if not await self.repo.get_by_id(id, tenant_id):
            raise NotFoundError("Branch not found.")
        branch = await self.repo.update(id, tenant_id, **data.model_dump(exclude_unset=True))
        await self.db.commit()
        return BranchResponse.model_validate(branch)

    async def activate(self, id: UUID, tenant_id: UUID) -> BranchResponse:
        if not await self.repo.get_by_id(id, tenant_id):
            raise NotFoundError("Branch not found.")
        branch = await self.repo.update(id, tenant_id, is_active=True)
        await self.db.commit()
        return BranchResponse.model_validate(branch)

    async def deactivate(self, id: UUID, tenant_id: UUID) -> BranchResponse:
        if not await self.repo.get_by_id(id, tenant_id):
            raise NotFoundError("Branch not found.")
        branch = await self.repo.update(id, tenant_id, is_active=False)
        await self.db.commit()
        return BranchResponse.model_validate(branch)

    async def delete(self, id: UUID, tenant_id: UUID) -> None:
        if not await self.repo.soft_delete(id, tenant_id):
            raise NotFoundError("Branch not found.")
        await self.db.commit()
