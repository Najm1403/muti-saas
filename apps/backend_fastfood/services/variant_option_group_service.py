# services/variant_option_group_service.py

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ConflictError, NotFoundError, ValidationError
from repositories.business_repository import BusinessRepository
from repositories.variant_option_group_repository import VariantOptionGroupRepository
from schemas.variant_option_group import (
    ProductVariantOptionAllowedSet,
    ProductVariantOptionGroupAttach,
    ProductVariantOptionGroupResponse,
    ProductVariantOptionGroupUpdate,
    VariantOptionGroupCreate,
    VariantOptionGroupResponse,
    VariantOptionGroupUpdate,
)


class VariantOptionGroupService:
    """
    Manages the Business-wide shared library of Variant Option Groups, and
    their attachment to individual products via ProductVariantOptionGroup.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = VariantOptionGroupRepository(db)
        self.business_repo = BusinessRepository(db)

    async def _verify_business(self, business_id: UUID, tenant_id: UUID) -> None:
        if not await self.business_repo.get_by_id(business_id, tenant_id):
            raise NotFoundError("Business not found.")

    # ---- shared library CRUD ----

    async def create(
        self, business_id: UUID, tenant_id: UUID, data: VariantOptionGroupCreate
    ) -> VariantOptionGroupResponse:
        await self._verify_business(business_id, tenant_id)
        group = await self.repo.create(
            business_id=business_id, name=data.name, description=data.description,
        )
        await self.db.commit()
        return VariantOptionGroupResponse.model_validate(group)

    async def get(self, id: UUID, tenant_id: UUID) -> VariantOptionGroupResponse:
        group = await self.repo.get_by_id(id, tenant_id)
        if not group:
            raise NotFoundError("Variant option group not found.")
        return VariantOptionGroupResponse.model_validate(group)

    async def list(self, business_id: UUID, tenant_id: UUID) -> list[VariantOptionGroupResponse]:
        await self._verify_business(business_id, tenant_id)
        groups = await self.repo.list(business_id=business_id, tenant_id=tenant_id)
        return [VariantOptionGroupResponse.model_validate(g) for g in groups]

    async def update(
        self, id: UUID, tenant_id: UUID, data: VariantOptionGroupUpdate
    ) -> VariantOptionGroupResponse:
        if not await self.repo.get_by_id(id, tenant_id):
            raise NotFoundError("Variant option group not found.")
        group = await self.repo.update(id, tenant_id, **data.model_dump(exclude_unset=True))
        await self.db.commit()
        return VariantOptionGroupResponse.model_validate(group)

    async def activate(self, id: UUID, tenant_id: UUID) -> VariantOptionGroupResponse:
        if not await self.repo.get_by_id(id, tenant_id):
            raise NotFoundError("Variant option group not found.")
        group = await self.repo.update(id, tenant_id, is_active=True)
        await self.db.commit()
        return VariantOptionGroupResponse.model_validate(group)

    async def deactivate(self, id: UUID, tenant_id: UUID) -> VariantOptionGroupResponse:
        if not await self.repo.get_by_id(id, tenant_id):
            raise NotFoundError("Variant option group not found.")
        group = await self.repo.update(id, tenant_id, is_active=False)
        await self.db.commit()
        return VariantOptionGroupResponse.model_validate(group)

    async def delete(self, id: UUID, tenant_id: UUID) -> None:
        if not await self.repo.soft_delete(id, tenant_id):
            raise NotFoundError("Variant option group not found.")
        await self.db.commit()

    # ---- product attachment ----

    async def _allowed_by_link(self, link_ids: list[UUID]) -> dict[UUID, list[UUID]]:
        from collections import defaultdict
        from sqlalchemy import select
        from models.product_variant_option_allowed import ProductVariantOptionAllowed

        if not link_ids:
            return {}
        rows = (await self.db.scalars(select(ProductVariantOptionAllowed).where(
            ProductVariantOptionAllowed.product_variant_option_group_id.in_(link_ids)))).all()
        result: dict[UUID, list[UUID]] = defaultdict(list)
        for row in rows:
            result[row.product_variant_option_group_id].append(row.variant_option_id)
        return result

    def _to_link_response(self, link, group, allowed_option_ids: list[UUID]) -> ProductVariantOptionGroupResponse:
        return ProductVariantOptionGroupResponse(
            id=link.id, product_id=link.product_id, option_group_id=link.option_group_id,
            is_required=link.is_required, display_order=link.display_order,
            usage_type=link.usage_type, min_selections=link.min_selections,
            max_selections=link.max_selections, default_option_id=link.default_option_id,
            allowed_option_ids=allowed_option_ids,
            name=group.name, description=group.description,
            source_category_id=link.source_category_id,
        )

    async def list_for_product(self, product_id: UUID, tenant_id: UUID) -> list[ProductVariantOptionGroupResponse]:
        from sqlalchemy import select
        from models.product import Product
        from models.category import Category
        from models.business import Business
        from models.product_variant_option_group import ProductVariantOptionGroup
        from models.variant_option_group import VariantOptionGroup

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
        rows = (await self.db.execute(
            select(ProductVariantOptionGroup, VariantOptionGroup)
            .join(VariantOptionGroup, ProductVariantOptionGroup.option_group_id == VariantOptionGroup.id)
            .where(ProductVariantOptionGroup.product_id == product_id, VariantOptionGroup.deleted_at.is_(None))
            .order_by(ProductVariantOptionGroup.display_order)
        )).all()
        allowed_by_link = await self._allowed_by_link([link.id for link, _ in rows])
        return [
            self._to_link_response(link, group, allowed_by_link.get(link.id, []))
            for link, group in rows
        ]

    async def attach_to_product(
        self, product_id: UUID, tenant_id: UUID, data: ProductVariantOptionGroupAttach
    ) -> ProductVariantOptionGroupResponse:
        from sqlalchemy import select
        from models.product import Product
        from models.category import Category
        from models.business import Business
        from models.product_variant_option_group import ProductVariantOptionGroup

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
                "Inventory components cannot have Variant Selections of their own. "
                "Attach this group to the configurable parent product instead."
            )
        group = await self.repo.get_by_id(data.option_group_id, tenant_id)
        if not group:
            raise NotFoundError("Variant option group not found.")
        existing = await self.db.scalar(select(ProductVariantOptionGroup).where(
            ProductVariantOptionGroup.product_id == product_id,
            ProductVariantOptionGroup.option_group_id == data.option_group_id))
        if existing:
            raise ConflictError("This group is already attached to the product.")
        if data.default_option_id is not None:
            await self._verify_default_option(data.option_group_id, data.default_option_id, tenant_id)
        from services.business_policy import enforce_variants_enabled
        await enforce_variants_enabled(self.db, tenant_id)
        link = ProductVariantOptionGroup(
            product_id=product_id, option_group_id=data.option_group_id,
            is_required=data.is_required, display_order=data.display_order,
            usage_type=data.usage_type, min_selections=data.min_selections,
            max_selections=data.max_selections, default_option_id=data.default_option_id,
        )
        self.db.add(link)
        await self.db.commit()
        await self.db.refresh(link)
        return self._to_link_response(link, group, [])

    async def _verify_default_option(self, option_group_id: UUID, option_id: UUID, tenant_id: UUID) -> None:
        from sqlalchemy import select
        from models.variant_option import VariantOption

        option = await self.db.scalar(select(VariantOption).where(
            VariantOption.id == option_id, VariantOption.option_group_id == option_group_id,
            VariantOption.deleted_at.is_(None)))
        if not option:
            raise ValidationError("default_option_id must be one of this group's own options.")

    async def update_attachment(
        self, product_id: UUID, tenant_id: UUID, link_id: UUID, data: ProductVariantOptionGroupUpdate
    ) -> ProductVariantOptionGroupResponse:
        from sqlalchemy import select
        from models.product_variant_option_group import ProductVariantOptionGroup
        from models.variant_option_group import VariantOptionGroup
        from models.variant import Variant

        link = await self.db.scalar(select(ProductVariantOptionGroup).where(
            ProductVariantOptionGroup.id == link_id, ProductVariantOptionGroup.product_id == product_id))
        if not link:
            raise NotFoundError("Attachment not found.")
        group = await self.repo.get_by_id(link.option_group_id, tenant_id)
        if not group:
            raise NotFoundError("Variant option group not found.")

        fields = data.model_dump(exclude_unset=True)
        if "usage_type" in fields and fields["usage_type"] != link.usage_type:
            # Switching a group to/from 'inventory_component' changes what
            # its selected values mean structurally (spec section 17) — block
            # while real combination Variants already cover it, exactly like
            # detaching (below), rather than leaving stale, meaningless rows.
            in_use = await self.db.scalar(select(Variant.id).where(
                Variant.product_id == product_id, Variant.deleted_at.is_(None),
                Variant.is_default.is_(False)).limit(1))
            if in_use:
                raise ConflictError(
                    "Remove this product's variant combinations before changing this group's usage type.")
        if "default_option_id" in fields and fields["default_option_id"] is not None:
            await self._verify_default_option(link.option_group_id, fields["default_option_id"], tenant_id)
        for key, value in fields.items():
            setattr(link, key, value)
        await self.db.commit()
        await self.db.refresh(link)
        allowed = (await self._allowed_by_link([link.id])).get(link.id, [])
        return self._to_link_response(link, group, allowed)

    async def set_allowed_options(
        self, product_id: UUID, tenant_id: UUID, link_id: UUID, data: ProductVariantOptionAllowedSet
    ) -> ProductVariantOptionGroupResponse:
        from sqlalchemy import delete, select
        from models.product_variant_option_group import ProductVariantOptionGroup
        from models.product_variant_option_allowed import ProductVariantOptionAllowed
        from models.variant_option import VariantOption

        link = await self.db.scalar(select(ProductVariantOptionGroup).where(
            ProductVariantOptionGroup.id == link_id, ProductVariantOptionGroup.product_id == product_id))
        if not link:
            raise NotFoundError("Attachment not found.")
        group = await self.repo.get_by_id(link.option_group_id, tenant_id)
        if not group:
            raise NotFoundError("Variant option group not found.")

        if data.variant_option_ids:
            valid = set((await self.db.scalars(select(VariantOption.id).where(
                VariantOption.id.in_(data.variant_option_ids),
                VariantOption.option_group_id == link.option_group_id,
                VariantOption.deleted_at.is_(None)))).all())
            if valid != set(data.variant_option_ids):
                raise ValidationError("Every allowed option must belong to this group.")
            if link.usage_type == "inventory_component":
                tracked = set((await self.db.scalars(select(VariantOption.id).where(
                    VariantOption.id.in_(data.variant_option_ids),
                    VariantOption.component_product_id.is_not(None),
                    VariantOption.deleted_at.is_(None),
                ))).all())
                if tracked != set(data.variant_option_ids):
                    raise ValidationError(
                        "Every selected component value must be set up for inventory tracking first."
                    )

        await self.db.execute(delete(ProductVariantOptionAllowed).where(
            ProductVariantOptionAllowed.product_variant_option_group_id == link_id))
        for option_id in data.variant_option_ids:
            self.db.add(ProductVariantOptionAllowed(
                product_variant_option_group_id=link_id, variant_option_id=option_id))
        await self.db.commit()
        return self._to_link_response(link, group, list(data.variant_option_ids))

    async def detach_from_product(self, product_id: UUID, tenant_id: UUID, link_id: UUID) -> None:
        from sqlalchemy import select
        from models.product_variant_option_group import ProductVariantOptionGroup
        from models.variant import Variant
        from models.variant_option import VariantOption

        link = await self.db.scalar(select(ProductVariantOptionGroup).where(
            ProductVariantOptionGroup.id == link_id, ProductVariantOptionGroup.product_id == product_id))
        if not link:
            raise NotFoundError("Attachment not found.")
        # Guard: detaching a group that generated combination Variants would
        # orphan their option_value_ids — block only while a live Variant
        # actually references one of THIS group's own options. Every
        # product always has at least its zero-option default Variant
        # (option_value_ids == [], spec D1), which never references any
        # group — checking "does any Variant exist at all" would always be
        # true and permanently block detaching an empty/unused group.
        group_option_ids = {str(oid) for oid in (await self.db.scalars(
            select(VariantOption.id).where(VariantOption.option_group_id == link.option_group_id)))}
        in_use = False
        if group_option_ids:
            variants = (await self.db.scalars(select(Variant).where(
                Variant.product_id == product_id, Variant.deleted_at.is_(None)))).all()
            in_use = any(group_option_ids & {str(oid) for oid in (v.option_value_ids or [])} for v in variants)
        if in_use:
            raise ConflictError(
                "Remove this product's variants before detaching a Variant Option Group.")
        await self.db.delete(link)
        await self.db.commit()
