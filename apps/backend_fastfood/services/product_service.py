# services/product_service.py

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ConflictError, NotFoundError, ValidationError
from models.branch import Branch
from models.category import Category
from models.product import Product
from models.product_branch import ProductBranch
from models.product_variant_option_group import ProductVariantOptionGroup
from models.product_addon_group import ProductAddonGroup
from models.product_spec import ProductSpec
from models.variant import Variant
from models.variant_option import VariantOption
from models.variant_option_group import VariantOptionGroup
from repositories.category_repository import CategoryRepository
from repositories.product_repository import ProductRepository
from schemas.branch_assignment import BranchAssignmentResponse, BranchBrief
from schemas.product import ProductCreate, ProductResponse, ProductUpdate
from schemas.product_spec import ProductSpecCreate, ProductSpecResponse, ProductSpecUpdate


class ProductService:
    """
    Manages products under a category, scoped to a tenant.

    Hierarchy enforced:
        tenant_id → business_id → category_id → product
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ProductRepository(db)
        self.category_repo = CategoryRepository(db)

    async def _verify_category(self, category_id: UUID, tenant_id: UUID) -> None:
        if not await self.category_repo.get_by_id(category_id, tenant_id):
            raise NotFoundError("Category not found.")

    async def create(
        self, category_id: UUID, tenant_id: UUID, data: ProductCreate
    ) -> ProductResponse:
        from services.ownership import catalog_references
        await catalog_references(self.db, tenant_id, data.model_dump(exclude_unset=True, exclude={"price"}))
        await self._verify_category(category_id, tenant_id)

        # A template with inventory.tracking_forced_on (D6) means every
        # variant must track — including the auto-seeded default one, so
        # the product itself must also carry allow_inventory_tracking=True.
        # Leaving either hardcoded to False would make product creation
        # impossible under such a template (enforce_tracking_policy would
        # reject the default variant unconditionally).
        from services.business_policy import load_business_policy
        policy = await load_business_policy(self.db, tenant_id)
        inventory_policy = policy.get("inventory", {}) or {}
        tracking_forced_on = bool(inventory_policy.get("tracking_forced_on"))
        tracking_default_on = bool(inventory_policy.get("tracking_default_on"))
        explicitly_set = "allow_inventory_tracking" in data.model_fields_set
        allow_tracking = (
            data.allow_inventory_tracking if explicitly_set
            else tracking_default_on
        ) or tracking_forced_on

        product = await self.repo.create(
            category_id=category_id,
            product_code=data.product_code,
            name=data.name,
            description=data.description,
            image_path=data.image_path,
            sku=data.sku,
            warranty=data.warranty,
            display_order=data.display_order,
            preparation_station_id=data.preparation_station_id,
            allow_inventory_tracking=allow_tracking,
        )
        # Apply branch assignment before creating the default Variant, so
        # opening_stock_by_branch (below) validates against the branches
        # actually being assigned here rather than the all_branches=True
        # DB default every product otherwise starts with.
        if data.branch_ids is not None or data.all_branches is not None:
            await self.set_branch_assignment(
                product.id, tenant_id,
                data.all_branches if data.all_branches is not None else True,
                data.branch_ids or [],
            )
        # Every product always gets a zero-option default Variant (spec D1) —
        # there is no product_id-only sale path anywhere in the system.
        from services.variant_service import VariantService
        variant_service = VariantService(self.db)
        default_variant = await variant_service.create(
            tenant_id, product.id, [], sale_price=data.price, cost_price=data.cost_price,
            tracks_inventory=allow_tracking,
            opening_stock_by_branch=data.opening_stock_by_branch,
        )
        product.default_variant_id = default_variant.id

        # Priced Variant Group (e.g. "Colors") — attaches a shared group as
        # usage_type='specification' and seeds one priced, stocked
        # combination Variant per selected value, all in this same
        # transaction. Never attached with zero satisfying variants — that
        # would leave a required group with nothing to cover it, and the
        # product permanently unsellable with no error anywhere (see
        # VariantService.compute_sellability).
        if data.priced_variant_group_id is not None and data.priced_variants:
            from repositories.variant_option_group_repository import VariantOptionGroupRepository
            from services.business_policy import enforce_variants_enabled

            group = await VariantOptionGroupRepository(self.db).get_by_id(
                data.priced_variant_group_id, tenant_id)
            if not group:
                raise NotFoundError("Variant option group not found.")
            await enforce_variants_enabled(self.db, tenant_id)

            link = ProductVariantOptionGroup(
                product_id=product.id, option_group_id=group.id,
                is_required=True, usage_type="specification",
                min_selections=1, max_selections=1,
            )
            self.db.add(link)
            await self.db.flush()

            for entry in data.priced_variants:
                await variant_service.create(
                    tenant_id, product.id, [entry.option_id],
                    sale_price=entry.sale_price, cost_price=entry.cost_price,
                    tracks_inventory=allow_tracking,
                    opening_stock_by_branch=entry.opening_stock_by_branch,
                )

        # Picks up whatever Variant Option Groups the category already
        # templates (e.g. every laptop in "Laptops" gets "RAM" and
        # "Storage" automatically) — see CategoryVariantOptionGroupService.
        from services.category_variant_option_group_service import CategoryVariantOptionGroupService
        await CategoryVariantOptionGroupService(self.db).sync_new_product(product.id, category_id)

        await self.db.commit()
        return await self.get(product.id, tenant_id)

    async def generate_sku(self, category_id: UUID, tenant_id: UUID) -> str:
        """Suggests a unique SKU: <CATEGORY-PREFIX>-<seq>, e.g. "LAP-0001".

        A convenience only — sku carries no DB-level uniqueness constraint
        (spec G2: optional, template-gated, never required), so this checks
        for collisions itself rather than relying on the database to catch
        one, and the tenant can freely edit or replace the suggestion before
        saving. Whether the SKU field is even shown, or required, is a
        frontend/business_policy concern (product_fields.sku) this endpoint
        has no opinion on — it only proposes a value when asked.
        """
        category = await self.category_repo.get_by_id(category_id, tenant_id)
        if not category:
            raise NotFoundError("Category not found.")

        prefix = "".join(ch for ch in category.name.upper() if ch.isalnum())[:3] or "SKU"
        existing_count = await self.db.scalar(
            select(func.count(Product.id))
            .join(Category, Product.category_id == Category.id)
            .where(Category.business_id == category.business_id, Product.sku.like(f"{prefix}-%"))
        )
        start = int(existing_count or 0) + 1
        for seq in range(start, start + 50):
            candidate = f"{prefix}-{seq:04d}"
            clash = await self.db.scalar(
                select(Product.id)
                .join(Category, Product.category_id == Category.id)
                .where(Category.business_id == category.business_id, Product.sku == candidate)
            )
            if not clash:
                return candidate
        raise ValidationError("Could not generate a unique SKU — enter one manually.")

    async def get(self, id: UUID, tenant_id: UUID) -> ProductResponse:
        product = await self.repo.get_by_id(id, tenant_id)
        if not product:
            raise NotFoundError("Product not found.")
        return await self._to_response(product)

    async def list(
        self,
        category_id: UUID,
        tenant_id: UUID,
        include_inactive: bool = False,
    ) -> list[ProductResponse]:
        await self._verify_category(category_id, tenant_id)
        products = await self.repo.list(
            category_id=category_id,
            tenant_id=tenant_id,
            include_inactive=include_inactive,
        )

        product_ids = [p.id for p in products]
        vog_counts: dict[UUID, int] = {}
        spec_counts: dict[UUID, int] = {}
        combination_product_ids: set[UUID] = set()
        addon_counts: dict[UUID, int] = {}
        prices: dict[UUID, object] = {}
        component_info: dict[UUID, tuple[UUID, str, str]] = {}
        if product_ids:
            rows = await self.db.execute(
                select(
                    VariantOption.component_product_id,
                    VariantOption.id,
                    VariantOption.name,
                    VariantOptionGroup.name,
                )
                .join(VariantOptionGroup, VariantOption.option_group_id == VariantOptionGroup.id)
                .where(
                    VariantOption.component_product_id.in_(product_ids),
                    VariantOption.deleted_at.is_(None),
                    VariantOptionGroup.deleted_at.is_(None),
                )
            )
            component_info = {
                product_id: (option_id, option_name, group_name)
                for product_id, option_id, option_name, group_name in rows.all()
            }

            rows = await self.db.execute(
                select(ProductVariantOptionGroup.product_id, func.count(ProductVariantOptionGroup.id))
                .where(ProductVariantOptionGroup.product_id.in_(product_ids))
                .group_by(ProductVariantOptionGroup.product_id)
            )
            vog_counts = {pid: n for pid, n in rows.all()}

            rows = await self.db.execute(
                select(ProductVariantOptionGroup.product_id, func.count(ProductVariantOptionGroup.id))
                .where(
                    ProductVariantOptionGroup.product_id.in_(product_ids),
                    ProductVariantOptionGroup.usage_type == "specification",
                )
                .group_by(ProductVariantOptionGroup.product_id)
            )
            spec_counts = {pid: n for pid, n in rows.all()}

            rows = await self.db.execute(
                select(Variant.product_id).where(
                    Variant.product_id.in_(product_ids),
                    Variant.is_default.is_(False),
                    Variant.deleted_at.is_(None),
                ).distinct()
            )
            combination_product_ids = {pid for (pid,) in rows.all()}

            rows = await self.db.execute(
                select(ProductAddonGroup.product_id, func.count(ProductAddonGroup.id))
                .where(ProductAddonGroup.product_id.in_(product_ids))
                .group_by(ProductAddonGroup.product_id)
            )
            addon_counts = {pid: n for pid, n in rows.all()}

            default_variant_ids = [p.default_variant_id for p in products if p.default_variant_id]
            if default_variant_ids:
                rows = await self.db.execute(
                    select(Variant.product_id, Variant.sale_price).where(Variant.id.in_(default_variant_ids))
                )
                prices = {pid: price for pid, price in rows.all()}

        result: list[ProductResponse] = []
        for p in products:
            resp = ProductResponse.model_validate(p)
            info = component_info.get(p.id)
            resp.is_inventory_component = info is not None
            if info:
                resp.component_option_id, resp.component_option_name, resp.component_group_name = info
            # Legacy recursive attachments are invalid for component SKUs and
            # are also ignored by POS sync and checkout.
            resp.variant_option_group_count = 0 if info else vog_counts.get(p.id, 0)
            resp.specification_group_count = 0 if info else spec_counts.get(p.id, 0)
            resp.has_combination_variants = p.id in combination_product_ids
            resp.addon_group_count = 0 if info else addon_counts.get(p.id, 0)
            resp.price = prices.get(p.id)
            result.append(resp)
        return result

    async def _to_response(self, product) -> ProductResponse:
        resp = ProductResponse.model_validate(product)
        component = (await self.db.execute(
            select(VariantOption.id, VariantOption.name, VariantOptionGroup.name)
            .join(VariantOptionGroup, VariantOption.option_group_id == VariantOptionGroup.id)
            .where(
                VariantOption.component_product_id == product.id,
                VariantOption.deleted_at.is_(None),
                VariantOptionGroup.deleted_at.is_(None),
            )
            .limit(1)
        )).first()
        resp.is_inventory_component = component is not None
        if component:
            resp.component_option_id, resp.component_option_name, resp.component_group_name = component
        resp.variant_option_group_count = await self.db.scalar(
            select(func.count(ProductVariantOptionGroup.id)).where(
                ProductVariantOptionGroup.product_id == product.id)) or 0
        resp.specification_group_count = await self.db.scalar(
            select(func.count(ProductVariantOptionGroup.id)).where(
                ProductVariantOptionGroup.product_id == product.id,
                ProductVariantOptionGroup.usage_type == "specification")) or 0
        resp.has_combination_variants = await self.db.scalar(
            select(Variant.id).where(
                Variant.product_id == product.id,
                Variant.is_default.is_(False),
                Variant.deleted_at.is_(None)).limit(1)) is not None
        resp.addon_group_count = await self.db.scalar(
            select(func.count(ProductAddonGroup.id)).where(
                ProductAddonGroup.product_id == product.id)) or 0
        if component:
            resp.variant_option_group_count = 0
            resp.specification_group_count = 0
            resp.addon_group_count = 0
        if product.default_variant_id:
            resp.price = await self.db.scalar(
                select(Variant.sale_price).where(Variant.id == product.default_variant_id))
        return resp

    async def update(
        self, id: UUID, tenant_id: UUID, data: ProductUpdate
    ) -> ProductResponse:
        from services.ownership import catalog_references
        await catalog_references(self.db, tenant_id, data.model_dump(exclude_unset=True))
        product = await self.repo.get_by_id(id, tenant_id)
        if not product:
            raise NotFoundError("Product not found.")
        old_category_id = product.category_id

        fields = data.model_dump(exclude_unset=True)
        component_option_id = await self.db.scalar(select(VariantOption.id).where(
            VariantOption.component_product_id == product.id,
            VariantOption.deleted_at.is_(None),
        ).limit(1))
        if component_option_id is not None:
            if fields.get("is_active") is False:
                raise ValidationError(
                    "This is a shared inventory component. Deactivate its value in the "
                    "Variant Options library so parent products and standalone sales stay consistent."
                )
            if fields.get("allow_inventory_tracking") is False:
                raise ValidationError("Shared inventory components must keep inventory tracking enabled.")
        if fields.get("allow_inventory_tracking") is False:
            from services.business_policy import load_business_policy
            policy = await load_business_policy(self.db, tenant_id)
            if bool((policy.get("inventory", {}) or {}).get("tracking_forced_on")):
                raise ValidationError(
                    "Inventory tracking is required by this Business Template."
                )
            # Cascade: a product that no longer allows tracking can't have
            # any variant still enforcing it — otherwise the variant is
            # silently orphaned (tracks_inventory stays True in the DB, but
            # every stock check ANDs both flags, so it just stops being
            # enforced with no visible signal, and "Enable tracking" never
            # re-offers it since the column already reads True). Existing
            # StockAdjustment/VariantBranchStock history is preserved — this
            # only stops tracking going forward, it doesn't erase records.
            await self.db.execute(
                update(Variant)
                .where(Variant.product_id == product.id, Variant.tracks_inventory.is_(True))
                .values(tracks_inventory=False)
            )
        requested_price = fields.pop("price", None)
        if requested_price is not None:
            # Only a product with real priced combination Variants (e.g.
            # Colors) needs its price edited per-variant instead — a
            # Specification-usage group attached with zero actual
            # combinations (nothing has ever been added to it yet, or an
            # Inventory Component group, which never generates combination
            # Variants at all) must not trip this guard, or the base price
            # becomes permanently uneditable with no way out.
            has_combinations = await self.db.scalar(
                select(Variant.id).where(
                    Variant.product_id == product.id,
                    Variant.is_default.is_(False),
                    Variant.deleted_at.is_(None),
                ).limit(1)
            ) is not None
            if has_combinations:
                raise ValidationError(
                    "This product has priced Variant combinations (e.g. Colors); "
                    "update each variant's own price instead."
                )
        product = await self.repo.update(id, tenant_id, **fields)
        if requested_price is not None:
            if not product.default_variant_id:
                raise ValidationError("This product has no default price to update.")
            default_variant = await self.db.scalar(
                select(Variant).where(Variant.id == product.default_variant_id)
            )
            if default_variant is None:
                raise ValidationError("This product has no default price to update.")
            default_variant.sale_price = requested_price

        new_category_id = fields.get("category_id")
        if new_category_id is not None and new_category_id != old_category_id:
            # Re-syncs this product's Variant Option Group attachments to
            # match its new category — see CategoryVariantOptionGroupService
            # .resync_product_category_change for exactly what moves,
            # re-parents, or detaches.
            from services.category_variant_option_group_service import CategoryVariantOptionGroupService
            await CategoryVariantOptionGroupService(self.db).resync_product_category_change(
                product.id, old_category_id, new_category_id,
            )

        await self.db.commit()
        return await self.get(product.id, tenant_id)

    async def activate(self, id: UUID, tenant_id: UUID) -> ProductResponse:
        if not await self.repo.get_by_id(id, tenant_id):
            raise NotFoundError("Product not found.")
        product = await self.repo.update(id, tenant_id, is_active=True)
        await self.db.commit()
        return await self.get(product.id, tenant_id)

    async def deactivate(self, id: UUID, tenant_id: UUID) -> ProductResponse:
        product = await self.repo.get_by_id(id, tenant_id)
        if not product:
            raise NotFoundError("Product not found.")
        component_option_id = await self.db.scalar(select(VariantOption.id).where(
            VariantOption.component_product_id == product.id,
            VariantOption.deleted_at.is_(None),
        ).limit(1))
        if component_option_id is not None:
            raise ValidationError(
                "This is a shared inventory component. Deactivate its value in the "
                "Variant Options library instead."
            )
        product = await self.repo.update(id, tenant_id, is_active=False)
        await self.db.commit()
        return await self.get(product.id, tenant_id)

    async def delete(self, id: UUID, tenant_id: UUID) -> None:
        product = await self.repo.get_by_id(id, tenant_id)
        if not product:
            raise NotFoundError("Product not found.")
        component_option_id = await self.db.scalar(select(VariantOption.id).where(
            VariantOption.component_product_id == product.id,
            VariantOption.deleted_at.is_(None),
        ).limit(1))
        if component_option_id is not None:
            raise ConflictError(
                "This product is the stock record for a shared Variant Option. "
                "Stop tracking that option first; components with stock or sale history cannot be removed."
            )
        if not await self.repo.soft_delete(id, tenant_id):
            raise NotFoundError("Product not found.")
        await self.db.commit()

    async def get_branch_assignment(
        self, product_id: UUID, tenant_id: UUID
    ) -> BranchAssignmentResponse:
        product = await self.repo.get_by_id(product_id, tenant_id)
        if not product:
            raise NotFoundError("Product not found.")
        if product.all_branches:
            return BranchAssignmentResponse(all_branches=True, branches=[])
        result = await self.db.execute(
            select(Branch)
            .join(ProductBranch, ProductBranch.branch_id == Branch.id)
            .where(ProductBranch.product_id == product_id)
            .where(Branch.deleted_at.is_(None))
            .order_by(Branch.name)
        )
        branches = result.scalars().all()
        return BranchAssignmentResponse(
            all_branches=False,
            branches=[BranchBrief(id=b.id, name=b.name, branch_code=b.branch_code) for b in branches],
        )

    async def set_branch_assignment(
        self, product_id: UUID, tenant_id: UUID, all_branches: bool, branch_ids: list[UUID]
    ) -> BranchAssignmentResponse:
        from services.ownership import tenant_branches
        branch_ids = await tenant_branches(self.db, tenant_id, branch_ids)
        product = await self.repo.get_by_id(product_id, tenant_id)
        if not product:
            raise NotFoundError("Product not found.")
        product.all_branches = all_branches
        await self.db.execute(
            delete(ProductBranch).where(ProductBranch.product_id == product_id)
        )
        assigned: list[Branch] = []
        if not all_branches and branch_ids:
            for bid in branch_ids:
                self.db.add(ProductBranch(branch_id=bid, product_id=product_id))
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

    # ================================================================
    # Specs — repeatable key/value rows (spec Part B / G2). Gated by
    # template.config.product_fields.specs on the frontend; never required.
    # ================================================================

    async def list_specs(self, product_id: UUID, tenant_id: UUID) -> list[ProductSpecResponse]:
        if not await self.repo.get_by_id(product_id, tenant_id):
            raise NotFoundError("Product not found.")
        rows = await self.db.scalars(
            select(ProductSpec).where(ProductSpec.product_id == product_id)
            .order_by(ProductSpec.sort_order, ProductSpec.created_at)
        )
        return [ProductSpecResponse.model_validate(r) for r in rows.all()]

    async def add_spec(self, product_id: UUID, tenant_id: UUID, data: ProductSpecCreate) -> ProductSpecResponse:
        if not await self.repo.get_by_id(product_id, tenant_id):
            raise NotFoundError("Product not found.")
        spec = ProductSpec(
            product_id=product_id,
            spec_key=data.spec_key,
            spec_value=data.spec_value,
            sort_order=data.sort_order,
        )
        self.db.add(spec)
        await self.db.commit()
        await self.db.refresh(spec)
        return ProductSpecResponse.model_validate(spec)

    async def _get_spec(self, product_id: UUID, spec_id: UUID, tenant_id: UUID) -> ProductSpec:
        if not await self.repo.get_by_id(product_id, tenant_id):
            raise NotFoundError("Product not found.")
        spec = await self.db.scalar(
            select(ProductSpec).where(ProductSpec.id == spec_id, ProductSpec.product_id == product_id)
        )
        if not spec:
            raise NotFoundError("Spec not found.")
        return spec

    async def update_spec(
        self, product_id: UUID, spec_id: UUID, tenant_id: UUID, data: ProductSpecUpdate
    ) -> ProductSpecResponse:
        spec = await self._get_spec(product_id, spec_id, tenant_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(spec, field, value)
        await self.db.commit()
        await self.db.refresh(spec)
        return ProductSpecResponse.model_validate(spec)

    async def delete_spec(self, product_id: UUID, spec_id: UUID, tenant_id: UUID) -> None:
        spec = await self._get_spec(product_id, spec_id, tenant_id)
        await self.db.delete(spec)
        await self.db.commit()
