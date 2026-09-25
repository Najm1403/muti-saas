# services/addon_group_service.py

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ConflictError, NotFoundError, ValidationError
from repositories.addon_group_repository import AddonGroupRepository
from repositories.business_repository import BusinessRepository
from schemas.addon_group import (
    AddonGroupCreate,
    AddonGroupResponse,
    AddonGroupUpdate,
    ProductAddonGroupAttach,
    ProductAddonGroupResponse,
)


class AddonGroupService:
    """
    Manages the Business-wide shared library of Add-on Groups, and their
    attachment to individual products via ProductAddonGroup. This section
    never talks to the Variant-generation logic (spec D4) — attaching an
    Add-on Group can never affect a product's combination_key.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = AddonGroupRepository(db)
        self.business_repo = BusinessRepository(db)

    async def _verify_business(self, business_id: UUID, tenant_id: UUID) -> None:
        if not await self.business_repo.get_by_id(business_id, tenant_id):
            raise NotFoundError("Business not found.")

    async def create(
        self, business_id: UUID, tenant_id: UUID, data: AddonGroupCreate
    ) -> AddonGroupResponse:
        await self._verify_business(business_id, tenant_id)
        group = await self.repo.create(
            business_id=business_id, name=data.name, selection_type=data.selection_type,
            min_select=data.min_select, max_select=data.max_select,
        )
        await self.db.commit()
        return AddonGroupResponse.model_validate(group)

    async def get(self, id: UUID, tenant_id: UUID) -> AddonGroupResponse:
        group = await self.repo.get_by_id(id, tenant_id)
        if not group:
            raise NotFoundError("Add-on group not found.")
        return AddonGroupResponse.model_validate(group)

    async def list(self, business_id: UUID, tenant_id: UUID) -> list[AddonGroupResponse]:
        await self._verify_business(business_id, tenant_id)
        groups = await self.repo.list(business_id=business_id, tenant_id=tenant_id)
        return [AddonGroupResponse.model_validate(g) for g in groups]

    async def update(
        self, id: UUID, tenant_id: UUID, data: AddonGroupUpdate
    ) -> AddonGroupResponse:
        if not await self.repo.get_by_id(id, tenant_id):
            raise NotFoundError("Add-on group not found.")
        group = await self.repo.update(id, tenant_id, **data.model_dump(exclude_unset=True))
        await self.db.commit()
        return AddonGroupResponse.model_validate(group)

    async def activate(self, id: UUID, tenant_id: UUID) -> AddonGroupResponse:
        if not await self.repo.get_by_id(id, tenant_id):
            raise NotFoundError("Add-on group not found.")
        group = await self.repo.update(id, tenant_id, is_active=True)
        await self.db.commit()
        return AddonGroupResponse.model_validate(group)

    async def deactivate(self, id: UUID, tenant_id: UUID) -> AddonGroupResponse:
        if not await self.repo.get_by_id(id, tenant_id):
            raise NotFoundError("Add-on group not found.")
        group = await self.repo.update(id, tenant_id, is_active=False)
        await self.db.commit()
        return AddonGroupResponse.model_validate(group)

    async def delete(self, id: UUID, tenant_id: UUID) -> None:
        if not await self.repo.soft_delete(id, tenant_id):
            raise NotFoundError("Add-on group not found.")
        await self.db.commit()

    # ---- product attachment ----

    async def list_for_product(self, product_id: UUID, tenant_id: UUID) -> list[ProductAddonGroupResponse]:
        from sqlalchemy import select
        from models.product import Product
        from models.category import Category
        from models.business import Business
        from models.product_addon_group import ProductAddonGroup
        from models.addon_group import AddonGroup

        product = await self.db.scalar(select(Product).join(Category, Product.category_id == Category.id)
            .join(Business, Category.business_id == Business.id).where(
                Product.id == product_id, Business.tenant_id == tenant_id, Product.deleted_at.is_(None)))
        if not product:
            raise NotFoundError("Product not found.")
        from models.variant_option import VariantOption
        is_component = await self.db.scalar(select(VariantOption.id).where(
            VariantOption.component_product_id == product.id,
            VariantOption.deleted_at.is_(None),
        ).limit(1)) is not None
        if is_component:
            return []
        rows = await self.db.execute(
            select(ProductAddonGroup, AddonGroup)
            .join(AddonGroup, ProductAddonGroup.addon_group_id == AddonGroup.id)
            .where(ProductAddonGroup.product_id == product_id, AddonGroup.deleted_at.is_(None))
            .order_by(ProductAddonGroup.display_order)
        )
        return [
            ProductAddonGroupResponse(
                id=link.id, product_id=link.product_id, addon_group_id=link.addon_group_id,
                display_order=link.display_order, name=group.name,
                selection_type=group.selection_type, min_select=group.min_select, max_select=group.max_select,
            )
            for link, group in rows.all()
        ]

    async def attach_to_product(
        self, product_id: UUID, tenant_id: UUID, data: ProductAddonGroupAttach
    ) -> ProductAddonGroupResponse:
        from sqlalchemy import select
        from models.product import Product
        from models.category import Category
        from models.business import Business
        from models.product_addon_group import ProductAddonGroup

        product = await self.db.scalar(select(Product).join(Category, Product.category_id == Category.id)
            .join(Business, Category.business_id == Business.id).where(
                Product.id == product_id, Business.tenant_id == tenant_id, Product.deleted_at.is_(None)))
        if not product:
            raise NotFoundError("Product not found.")
        from models.variant_option import VariantOption
        is_component = await self.db.scalar(select(VariantOption.id).where(
            VariantOption.component_product_id == product.id,
            VariantOption.deleted_at.is_(None),
        ).limit(1)) is not None
        if is_component:
            raise ValidationError(
                "Inventory components cannot have Add-on Groups of their own. "
                "Attach add-ons to the configurable parent product instead."
            )
        group = await self.repo.get_by_id(data.addon_group_id, tenant_id)
        if not group:
            raise NotFoundError("Add-on group not found.")
        existing = await self.db.scalar(select(ProductAddonGroup).where(
            ProductAddonGroup.product_id == product_id,
            ProductAddonGroup.addon_group_id == data.addon_group_id))
        if existing:
            raise ConflictError("This group is already attached to the product.")
        from services.business_policy import enforce_addons_enabled
        await enforce_addons_enabled(self.db, tenant_id)
        link = ProductAddonGroup(
            product_id=product_id, addon_group_id=data.addon_group_id, display_order=data.display_order,
        )
        self.db.add(link)
        await self.db.commit()
        await self.db.refresh(link)
        return ProductAddonGroupResponse(
            id=link.id, product_id=link.product_id, addon_group_id=link.addon_group_id,
            display_order=link.display_order, name=group.name,
            selection_type=group.selection_type, min_select=group.min_select, max_select=group.max_select,
        )

    async def detach_from_product(self, product_id: UUID, tenant_id: UUID, link_id: UUID) -> None:
        from sqlalchemy import select
        from models.product_addon_group import ProductAddonGroup

        link = await self.db.scalar(select(ProductAddonGroup).where(
            ProductAddonGroup.id == link_id, ProductAddonGroup.product_id == product_id))
        if not link:
            raise NotFoundError("Attachment not found.")
        await self.db.delete(link)
        await self.db.commit()
