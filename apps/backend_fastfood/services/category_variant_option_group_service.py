# services/category_variant_option_group_service.py
#
# Manages a Category's Variant Option Group templates
# (CategoryVariantOptionGroup) and cascades them onto the category's
# products' own ProductVariantOptionGroup attachments, so an admin
# configures a shared group like "RAM" once per category instead of once
# per product.
#
# What cascades and what doesn't (see CategoryVariantOptionGroupUpdate's
# docstring for the reasoning):
#   - Attaching a group to a category attaches it to every existing,
#     non-component product in that category (skipping ones that already
#     have it, whatever the origin).
#   - Detaching a group from a category detaches it from every product
#     whose attachment traces back to THIS category (source_category_id),
#     skipping any a live Variant still depends on — exactly like a manual
#     per-product detach's own safety check.
#   - Editing a category template's fields (is_required, etc.) only changes
#     the template — it does NOT retroactively push into products that
#     already have their own row, so a product's own customization is
#     never silently overwritten.
#   - A NEW product created under a category, or a product moved INTO a
#     category, picks up that category's current templates (see
#     sync_new_product / resync_product_category_change, called from
#     ProductService). A product moved OUT of a category has its
#     old-category-sourced groups detached (same live-Variant safety net)
#     unless the new category also defines them, in which case the
#     attachment is simply re-parented (source_category_id updated) so any
#     per-product customization (e.g. allowed-options) survives.
#
# A manually/one-off attached group (ProductVariantOptionGroup with
# source_category_id NULL — see that model's docstring) is never touched by
# any of this — only rows this service itself created are ever auto-detached.

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ConflictError, NotFoundError, ValidationError
from models.category_variant_option_group import CategoryVariantOptionGroup
from models.product import Product
from models.product_variant_option_group import ProductVariantOptionGroup
from models.variant import Variant
from models.variant_option import VariantOption
from models.variant_option_group import VariantOptionGroup
from repositories.category_repository import CategoryRepository
from repositories.variant_option_group_repository import VariantOptionGroupRepository
from schemas.variant_option_group import (
    CategoryVariantOptionGroupAttach,
    CategoryVariantOptionGroupResponse,
    CategoryVariantOptionGroupUpdate,
)


class CategoryVariantOptionGroupService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.group_repo = VariantOptionGroupRepository(db)
        self.category_repo = CategoryRepository(db)

    async def _verify_category(self, category_id: UUID, tenant_id: UUID):
        category = await self.category_repo.get_by_id(category_id, tenant_id)
        if not category:
            raise NotFoundError("Category not found.")
        return category

    async def _verify_default_option(self, option_group_id: UUID, option_id: UUID, tenant_id: UUID) -> None:
        option = await self.db.scalar(select(VariantOption).where(
            VariantOption.id == option_id, VariantOption.option_group_id == option_group_id,
            VariantOption.deleted_at.is_(None)))
        if not option:
            raise ValidationError("default_option_id must be one of this group's own options.")

    def _to_response(self, link: CategoryVariantOptionGroup, group: VariantOptionGroup) -> CategoryVariantOptionGroupResponse:
        return CategoryVariantOptionGroupResponse(
            id=link.id, category_id=link.category_id, option_group_id=link.option_group_id,
            is_required=link.is_required, display_order=link.display_order,
            min_selections=link.min_selections, max_selections=link.max_selections,
            default_option_id=link.default_option_id,
            name=group.name, description=group.description,
        )

    # ---- category template CRUD ----

    async def list_for_category(self, category_id: UUID, tenant_id: UUID) -> list[CategoryVariantOptionGroupResponse]:
        await self._verify_category(category_id, tenant_id)
        rows = (await self.db.execute(
            select(CategoryVariantOptionGroup, VariantOptionGroup)
            .join(VariantOptionGroup, CategoryVariantOptionGroup.option_group_id == VariantOptionGroup.id)
            .where(CategoryVariantOptionGroup.category_id == category_id, VariantOptionGroup.deleted_at.is_(None))
            .order_by(CategoryVariantOptionGroup.display_order)
        )).all()
        return [self._to_response(link, group) for link, group in rows]

    async def attach_to_category(
        self, category_id: UUID, tenant_id: UUID, data: CategoryVariantOptionGroupAttach
    ) -> CategoryVariantOptionGroupResponse:
        await self._verify_category(category_id, tenant_id)
        group = await self.group_repo.get_by_id(data.option_group_id, tenant_id)
        if not group:
            raise NotFoundError("Variant option group not found.")
        existing = await self.db.scalar(select(CategoryVariantOptionGroup).where(
            CategoryVariantOptionGroup.category_id == category_id,
            CategoryVariantOptionGroup.option_group_id == data.option_group_id))
        if existing:
            raise ConflictError("This group is already attached to the category.")
        if data.default_option_id is not None:
            await self._verify_default_option(data.option_group_id, data.default_option_id, tenant_id)

        from services.business_policy import enforce_variants_enabled
        await enforce_variants_enabled(self.db, tenant_id)

        link = CategoryVariantOptionGroup(
            category_id=category_id, option_group_id=data.option_group_id,
            is_required=data.is_required, display_order=data.display_order,
            min_selections=data.min_selections, max_selections=data.max_selections,
            default_option_id=data.default_option_id,
        )
        self.db.add(link)
        await self.db.flush()

        await self._cascade_attach_to_products(category_id, link)

        await self.db.commit()
        await self.db.refresh(link)
        return self._to_response(link, group)

    async def update_attachment(
        self, category_id: UUID, tenant_id: UUID, link_id: UUID, data: CategoryVariantOptionGroupUpdate
    ) -> CategoryVariantOptionGroupResponse:
        await self._verify_category(category_id, tenant_id)
        link = await self.db.scalar(select(CategoryVariantOptionGroup).where(
            CategoryVariantOptionGroup.id == link_id, CategoryVariantOptionGroup.category_id == category_id))
        if not link:
            raise NotFoundError("Attachment not found.")
        group = await self.group_repo.get_by_id(link.option_group_id, tenant_id)
        if not group:
            raise NotFoundError("Variant option group not found.")

        fields = data.model_dump(exclude_unset=True)
        if "default_option_id" in fields and fields["default_option_id"] is not None:
            await self._verify_default_option(link.option_group_id, fields["default_option_id"], tenant_id)
        for key, value in fields.items():
            setattr(link, key, value)
        await self.db.commit()
        await self.db.refresh(link)
        return self._to_response(link, group)

    async def detach_from_category(self, category_id: UUID, tenant_id: UUID, link_id: UUID) -> tuple[int, int]:
        """Returns (detached_count, skipped_count) — skipped means a live
        Variant on that product still depends on the group, mirroring
        VariantOptionGroupService.detach_from_product's own guard."""
        await self._verify_category(category_id, tenant_id)
        link = await self.db.scalar(select(CategoryVariantOptionGroup).where(
            CategoryVariantOptionGroup.id == link_id, CategoryVariantOptionGroup.category_id == category_id))
        if not link:
            raise NotFoundError("Attachment not found.")
        option_group_id = link.option_group_id
        await self.db.delete(link)
        await self.db.flush()

        rows = (await self.db.scalars(select(ProductVariantOptionGroup).where(
            ProductVariantOptionGroup.source_category_id == category_id,
            ProductVariantOptionGroup.option_group_id == option_group_id))).all()
        detached = skipped = 0
        for row in rows:
            if await self._try_detach(row.product_id, row):
                detached += 1
            else:
                skipped += 1
        await self.db.commit()
        return detached, skipped

    # ---- cascade primitives (also called from ProductService) ----

    async def sync_new_product(self, product_id: UUID, category_id: UUID | None) -> None:
        """Attaches every template of `category_id` to a freshly created
        product. No-op for a component product or a categoryless product."""
        if category_id is None:
            return
        templates = (await self.db.scalars(select(CategoryVariantOptionGroup).where(
            CategoryVariantOptionGroup.category_id == category_id))).all()
        for template in templates:
            await self._attach_group_to_product(product_id, template, category_id)
        await self.db.flush()

    async def resync_product_category_change(
        self, product_id: UUID, old_category_id: UUID | None, new_category_id: UUID | None,
    ) -> None:
        """Called when an existing product's category changes. Re-parents
        attachments the new category also defines (keeping any per-product
        customization), detaches ones it doesn't (unless a live Variant
        blocks it), and attaches whatever new templates aren't already
        present."""
        new_templates = (await self.db.scalars(select(CategoryVariantOptionGroup).where(
            CategoryVariantOptionGroup.category_id == new_category_id))).all() if new_category_id else []
        new_group_ids = {t.option_group_id for t in new_templates}

        if old_category_id is not None:
            old_rows = (await self.db.scalars(select(ProductVariantOptionGroup).where(
                ProductVariantOptionGroup.product_id == product_id,
                ProductVariantOptionGroup.source_category_id == old_category_id))).all()
            for row in old_rows:
                if row.option_group_id in new_group_ids:
                    row.source_category_id = new_category_id
                else:
                    await self._try_detach(product_id, row)

        for template in new_templates:
            await self._attach_group_to_product(product_id, template, new_category_id)
        await self.db.flush()

    async def _cascade_attach_to_products(
        self, category_id: UUID, link: CategoryVariantOptionGroup,
    ) -> None:
        """Attaches a freshly-created category template to every existing,
        non-component product in the category — batched into a fixed
        number of queries plus one bulk insert, instead of looping
        per-product (3 queries + a flush each; a 200-product category would
        otherwise mean ~600 round-trips for one "attach group to category"
        action)."""
        product_ids = (await self.db.scalars(select(Product.id).where(
            Product.category_id == category_id, Product.deleted_at.is_(None)))).all()
        if not product_ids:
            return

        component_product_ids = set((await self.db.scalars(select(VariantOption.component_product_id).where(
            VariantOption.component_product_id.in_(product_ids),
            VariantOption.deleted_at.is_(None),
        ))).all())
        already_attached = set((await self.db.scalars(select(ProductVariantOptionGroup.product_id).where(
            ProductVariantOptionGroup.product_id.in_(product_ids),
            ProductVariantOptionGroup.option_group_id == link.option_group_id,
        ))).all())

        targets = [pid for pid in product_ids if pid not in component_product_ids and pid not in already_attached]
        if not targets:
            return
        self.db.add_all([
            ProductVariantOptionGroup(
                product_id=product_id, option_group_id=link.option_group_id,
                is_required=link.is_required, display_order=link.display_order,
                usage_type="inventory_component",
                min_selections=link.min_selections, max_selections=link.max_selections,
                default_option_id=link.default_option_id,
                source_category_id=category_id,
            )
            for product_id in targets
        ])
        await self.db.flush()

    async def _attach_group_to_product(
        self, product_id: UUID, template: CategoryVariantOptionGroup, category_id: UUID,
    ) -> None:
        if await self._is_inventory_component(product_id):
            return
        existing = await self.db.scalar(select(ProductVariantOptionGroup.id).where(
            ProductVariantOptionGroup.product_id == product_id,
            ProductVariantOptionGroup.option_group_id == template.option_group_id))
        if existing:
            return
        self.db.add(ProductVariantOptionGroup(
            product_id=product_id, option_group_id=template.option_group_id,
            is_required=template.is_required, display_order=template.display_order,
            usage_type="inventory_component",
            min_selections=template.min_selections, max_selections=template.max_selections,
            default_option_id=template.default_option_id,
            source_category_id=category_id,
        ))
        await self.db.flush()

    async def _is_inventory_component(self, product_id: UUID) -> bool:
        return await self.db.scalar(select(VariantOption.id).where(
            VariantOption.component_product_id == product_id,
            VariantOption.deleted_at.is_(None),
        ).limit(1)) is not None

    async def _try_detach(self, product_id: UUID, link: ProductVariantOptionGroup) -> bool:
        """Best-effort detach mirroring VariantOptionGroupService
        .detach_from_product's live-Variant safety check — returns False
        (leaving the row in place) instead of raising, since this runs
        unattended inside a bulk cascade over many products."""
        group_option_ids = {str(oid) for oid in (await self.db.scalars(
            select(VariantOption.id).where(VariantOption.option_group_id == link.option_group_id)))}
        if group_option_ids:
            variants = (await self.db.scalars(select(Variant).where(
                Variant.product_id == product_id, Variant.deleted_at.is_(None)))).all()
            if any(group_option_ids & {str(oid) for oid in (v.option_value_ids or [])} for v in variants):
                return False
        await self.db.delete(link)
        await self.db.flush()
        return True
