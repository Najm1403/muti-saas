# services/variant_option_service.py

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ConflictError, NotFoundError
from repositories.variant_option_group_repository import VariantOptionGroupRepository
from repositories.variant_option_repository import VariantOptionRepository
from schemas.variant_option import (
    VariantOptionComponentSet,
    VariantOptionCreate,
    VariantOptionResponse,
    VariantOptionUpdate,
)


class VariantOptionService:
    """
    Manages options under a Variant Option Group, scoped to a tenant.

    Hierarchy enforced:
        tenant_id → business → variant_option_group → variant_option
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = VariantOptionRepository(db)
        self.group_repo = VariantOptionGroupRepository(db)

    async def _verify_group(self, option_group_id: UUID, tenant_id: UUID) -> None:
        if not await self.group_repo.get_by_id(option_group_id, tenant_id):
            raise NotFoundError("Variant option group not found.")

    async def create(
        self, option_group_id: UUID, tenant_id: UUID, data: VariantOptionCreate
    ) -> VariantOptionResponse:
        await self._verify_group(option_group_id, tenant_id)
        option = await self.repo.create(
            option_group_id=option_group_id,
            name=data.name,
            display_order=data.display_order,
        )
        await self.db.commit()
        return VariantOptionResponse.model_validate(option)

    async def get(self, id: UUID, tenant_id: UUID) -> VariantOptionResponse:
        option = await self.repo.get_by_id(id, tenant_id)
        if not option:
            raise NotFoundError("Variant option not found.")
        return VariantOptionResponse.model_validate(option)

    async def list(
        self, option_group_id: UUID, tenant_id: UUID
    ) -> list[VariantOptionResponse]:
        await self._verify_group(option_group_id, tenant_id)
        options = await self.repo.list(
            option_group_id=option_group_id, tenant_id=tenant_id
        )
        return [VariantOptionResponse.model_validate(o) for o in options]

    async def update(
        self, id: UUID, tenant_id: UUID, data: VariantOptionUpdate
    ) -> VariantOptionResponse:
        if not await self.repo.get_by_id(id, tenant_id):
            raise NotFoundError("Variant option not found.")
        option = await self.repo.update(id, tenant_id, **data.model_dump(exclude_unset=True))
        await self.db.commit()
        return VariantOptionResponse.model_validate(option)

    async def activate(self, id: UUID, tenant_id: UUID) -> VariantOptionResponse:
        if not await self.repo.get_by_id(id, tenant_id):
            raise NotFoundError("Variant option not found.")
        option = await self.repo.update(id, tenant_id, is_active=True)
        await self.db.commit()
        return VariantOptionResponse.model_validate(option)

    async def deactivate(self, id: UUID, tenant_id: UUID) -> VariantOptionResponse:
        if not await self.repo.get_by_id(id, tenant_id):
            raise NotFoundError("Variant option not found.")
        option = await self.repo.update(id, tenant_id, is_active=False)
        await self.db.commit()
        return VariantOptionResponse.model_validate(option)

    async def delete(self, id: UUID, tenant_id: UUID) -> None:
        if not await self.repo.soft_delete(id, tenant_id):
            raise NotFoundError("Variant option not found.")
        await self.db.commit()

    # ================================================================
    # Shared inventory component (Laptop Store shareable-inventory model)
    # ================================================================

    async def set_inventory_component(
        self, id: UUID, tenant_id: UUID, data: VariantOptionComponentSet
    ) -> VariantOptionResponse:
        """Marks this shared option as an independently-stocked inventory
        component — auto-creates ONE small real Product (its own default
        Variant, under a lazily-created "Components" category) that this
        option now represents, reusing the existing Product/Variant/
        VariantBranchStock stock engine unchanged. Every product that later
        attaches this option's group with usage_type='inventory_component'
        (services/variant_option_group_service.py) automatically shares
        this one stock pool — no further per-product linking step.

        A no-op if this option is already tracked — use the normal
        PATCH /variants/{id} and stock endpoints against the returned
        component_product_id's default_variant_id to change price/stock
        afterward, rather than a second code path here.
        """
        option = await self.repo.get_by_id(id, tenant_id)
        if not option:
            raise NotFoundError("Variant option not found.")
        if option.component_product_id:
            return VariantOptionResponse.model_validate(option)

        group = await self.group_repo.get_by_id(option.option_group_id, tenant_id)
        if not group:
            raise NotFoundError("Variant option group not found.")

        from models.category import Category
        category = await self.db.scalar(select(Category).where(
            Category.business_id == group.business_id, Category.name == "Components",
            Category.deleted_at.is_(None)))
        if category is None:
            category = Category(
                business_id=group.business_id, name="Components",
                description="Auto-created to hold shared inventory components (RAM, SSDs, "
                             "batteries, etc.) tracked from the Variant Options library.",
            )
            self.db.add(category)
            await self.db.flush()

        from repositories.product_repository import ProductRepository
        from services.variant_service import VariantService

        # product_code only needs to be unique within the category (spec:
        # optional/never required) — derived from the option id, not its
        # name, since two different groups may share an option name.
        product = await ProductRepository(self.db).create(
            category_id=category.id, product_code=f"COMP-{str(option.id)[:8].upper()}",
            name=option.name, allow_inventory_tracking=True,
        )
        variant = await VariantService(self.db).create(
            tenant_id, product.id, [], sale_price=data.sale_price, cost_price=data.cost_price,
            tracks_inventory=True,
            opening_stock_by_branch=data.opening_stock_by_branch,
        )
        product.default_variant_id = variant.id
        option.component_product_id = product.id
        await self.db.commit()
        await self.db.refresh(option)
        return VariantOptionResponse.model_validate(option)

    async def unset_inventory_component(self, id: UUID, tenant_id: UUID) -> VariantOptionResponse:
        """Stops treating this option as a shared inventory component —
        blocked (same guard as VariantService.delete()) while its component
        Variant still has stock anywhere or has ever been sold, so this can
        never silently discard real inventory or sale history. The backing
        Product itself is left alone (it's a real, independently sellable
        product) — this only detaches the option's pointer to it."""
        option = await self.repo.get_by_id(id, tenant_id)
        if not option:
            raise NotFoundError("Variant option not found.")
        if not option.component_product_id:
            return VariantOptionResponse.model_validate(option)

        from models.product import Product
        product = await self.db.scalar(select(Product).where(Product.id == option.component_product_id))
        if product is not None and product.default_variant_id:
            from services.variant_service import VariantService
            variant_svc = VariantService(self.db)
            variant = await variant_svc.get(tenant_id, product.default_variant_id)
            stock = await variant_svc.stock_snapshot(variant)
            if stock and any(qty for qty in stock.values()):
                raise ConflictError(
                    "This component still has stock at one or more branches — "
                    "clear it to zero before untracking.")
            from models.sale_item import SaleItem
            ever_sold = await self.db.scalar(select(SaleItem.id).where(
                SaleItem.variant_id == product.default_variant_id).limit(1))
            if ever_sold is not None:
                raise ConflictError(
                    "This component has sale history and can't be untracked.")

        option.component_product_id = None
        await self.db.commit()
        await self.db.refresh(option)
        return VariantOptionResponse.model_validate(option)
