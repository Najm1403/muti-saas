# services/pos_sync_service.py
#
# Builds the menu/settings payloads that the POS app downloads on startup
# (full sync) and at regular intervals (delta sync — currently implemented
# as a full re-fetch; see api/v1/pos/sync.py).
#
# Branch-awareness: products/deals/promotions respect the all_branches flag.
# If all_branches=True the item is available everywhere; if False only branches
# explicitly listed in the join table receive it.

from __future__ import annotations

from datetime import datetime, timezone
import base64
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from models.branch import Branch
from models.branch_deal import BranchDeal
from models.product_branch import ProductBranch
from models.branch_promotion import BranchPromotion
from models.category import Category
from models.deal import Deal
from models.deal_item import DealItem
from models.product import Product
from models.product_addon_group import ProductAddonGroup
from models.product_variant_option_group import ProductVariantOptionGroup
from models.addon_group import AddonGroup
from models.addon_item import AddonItem
from models.variant_option_group import VariantOptionGroup
from models.variant_option import VariantOption
from models.promotion import Promotion
from models.business import Business
from models.tax_rate import TaxRate
from core.exceptions import NotFoundError
from schemas.pos_sync import (
    PosDeltaSyncResponse,
    PosSyncAddonGroup,
    PosSyncAddonItem,
    PosSyncCategory,
    PosSyncDeal,
    PosSyncDealItem,
    PosSyncVariantOption,
    PosSyncVariantOptionGroup,
    PosSyncProduct,
    PosSyncPromotion,
    PosSyncResponse,
    PosSyncTaxRate,
)


class PosSyncService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _get_branch(self, branch_id: UUID, tenant_id: UUID) -> Branch:
        result = await self.db.execute(
            select(Branch)
            .join(Business, Branch.business_id == Business.id)
            .where(
                Branch.id == branch_id,
                Business.tenant_id == tenant_id,
                Branch.deleted_at.is_(None),
                Business.deleted_at.is_(None),
            )
        )
        branch = result.scalar_one_or_none()
        if not branch:
            raise NotFoundError("Branch not found.")
        return branch

    async def _categories(
        self, business_id: UUID, since: datetime | None
    ) -> list[PosSyncCategory]:
        stmt = select(Category).where(
            Category.business_id == business_id,
            Category.deleted_at.is_(None),
        )
        if since:
            stmt = stmt.where(Category.updated_at > since)
        result = await self.db.execute(stmt.order_by(Category.display_order))
        return [
            PosSyncCategory(
                id=c.id,
                name=c.name,
                description=c.description,
                image_path=c.image_path,
                display_order=c.display_order,
                is_active=c.is_active,
            )
            for c in result.scalars().all()
        ]

    async def _products(
        self, business_id: UUID, branch_id: UUID, since: datetime | None
    ) -> list[PosSyncProduct]:
        stmt = (
            select(Product)
            .join(Category, Product.category_id == Category.id)
            .where(
                Category.business_id == business_id,
                Product.deleted_at.is_(None),
                Category.deleted_at.is_(None),
            )
        )
        if since:
            stmt = stmt.where(Product.updated_at > since)

        result = await self.db.execute(stmt.order_by(Product.display_order))
        all_products = result.scalars().all()

        # Filter by branch assignment.
        branch_specific_ids: set[UUID] = await self._branch_product_ids(branch_id)
        products = [p for p in all_products if p.all_branches or p.id in branch_specific_ids]
        if not products:
            return []
        product_ids = [p.id for p in products]

        # Component SKUs remain independently sellable products, but they are
        # leaves in the configuration graph. Ignore legacy recursive links.
        component_product_rows = await self.db.scalars(select(
            VariantOption.component_product_id
        ).where(
            VariantOption.component_product_id.in_(product_ids),
            VariantOption.deleted_at.is_(None),
        ))
        component_catalog_product_ids = set(component_product_rows.all())
        configurable_product_ids = set(product_ids) - component_catalog_product_ids

        # Default variant price per product.
        from models.variant import Variant
        default_ids = [p.default_variant_id for p in products if p.default_variant_id]
        prices = {}
        if default_ids:
            rows = await self.db.execute(select(Variant.id, Variant.sale_price).where(Variant.id.in_(default_ids)))
            prices = {vid: price for vid, price in rows.all()}

        # Attached Variant Option Groups (shared, via join table).
        link_rows = await self.db.execute(
            select(ProductVariantOptionGroup, VariantOptionGroup)
            .join(VariantOptionGroup, ProductVariantOptionGroup.option_group_id == VariantOptionGroup.id)
            .where(
                ProductVariantOptionGroup.product_id.in_(configurable_product_ids),
                VariantOptionGroup.deleted_at.is_(None),
                VariantOptionGroup.is_active.is_(True),
            )
        )
        links = link_rows.all()
        group_ids = {group.id for _, group in links}
        options_by_group: dict[UUID, list[VariantOption]] = {}
        if group_ids:
            opt_rows = await self.db.scalars(select(VariantOption).where(
                VariantOption.option_group_id.in_(group_ids),
                VariantOption.deleted_at.is_(None), VariantOption.is_active.is_(True),
            ).order_by(VariantOption.display_order))
            for o in opt_rows.all():
                options_by_group.setdefault(o.option_group_id, []).append(o)

        # Shared inventory components (Laptop Store model) — resolve each
        # option's own default Variant so the POS can price/stock it via the
        # `variants` list it already syncs, no separate data stream needed.
        component_product_ids = {o.component_product_id for opts in options_by_group.values()
                                  for o in opts if o.component_product_id}
        component_variant_by_product: dict[UUID, UUID] = {}
        if component_product_ids:
            rows = await self.db.execute(select(Product.id, Product.default_variant_id).where(
                Product.id.in_(component_product_ids)))
            component_variant_by_product = {pid: vid for pid, vid in rows.all() if vid is not None}

        # Per-product restriction on which of a group's shared options apply
        # (spec §22 — "compatibility is product-specific"); empty = every
        # option above is offered.
        from models.product_variant_option_allowed import ProductVariantOptionAllowed
        link_ids = {link.id for link, _ in links}
        allowed_by_link: dict[UUID, list[UUID]] = {}
        if link_ids:
            allowed_rows = await self.db.execute(select(
                ProductVariantOptionAllowed.product_variant_option_group_id,
                ProductVariantOptionAllowed.variant_option_id,
            ).where(ProductVariantOptionAllowed.product_variant_option_group_id.in_(link_ids)))
            for link_id, option_id in allowed_rows.all():
                allowed_by_link.setdefault(link_id, []).append(option_id)

        vogs_by_product: dict[UUID, list[PosSyncVariantOptionGroup]] = {}
        for link, group in links:
            vogs_by_product.setdefault(link.product_id, []).append(
                PosSyncVariantOptionGroup(
                    id=group.id,
                    product_id=link.product_id,
                    name=group.name,
                    is_required=link.is_required,
                    display_order=link.display_order,
                    usage_type=link.usage_type,
                    allowed_option_ids=allowed_by_link.get(link.id, []),
                    options=[
                        PosSyncVariantOption(
                            id=o.id, option_group_id=o.option_group_id, name=o.name,
                            display_order=o.display_order, is_active=o.is_active,
                            component_variant_id=component_variant_by_product.get(o.component_product_id)
                                if o.component_product_id else None,
                        )
                        for o in options_by_group.get(group.id, [])
                    ],
                )
            )

        # Attached Add-on Groups (shared, via join table) — never feeds
        # variant generation (spec A1/D4).
        addon_link_rows = await self.db.execute(
            select(ProductAddonGroup, AddonGroup)
            .join(AddonGroup, ProductAddonGroup.addon_group_id == AddonGroup.id)
            .where(
                ProductAddonGroup.product_id.in_(configurable_product_ids),
                AddonGroup.deleted_at.is_(None),
                AddonGroup.is_active.is_(True),
            )
        )
        addon_links = addon_link_rows.all()
        addon_group_ids = {group.id for _, group in addon_links}
        items_by_group: dict[UUID, list[AddonItem]] = {}
        if addon_group_ids:
            item_rows = await self.db.scalars(select(AddonItem).where(
                AddonItem.addon_group_id.in_(addon_group_ids),
                AddonItem.deleted_at.is_(None), AddonItem.is_active.is_(True),
            ).order_by(AddonItem.display_order))
            for i in item_rows.all():
                items_by_group.setdefault(i.addon_group_id, []).append(i)

        addons_by_product: dict[UUID, list[PosSyncAddonGroup]] = {}
        for link, group in addon_links:
            addons_by_product.setdefault(link.product_id, []).append(
                PosSyncAddonGroup(
                    id=group.id,
                    product_id=link.product_id,
                    name=group.name,
                    selection_type=group.selection_type,
                    min_select=group.min_select,
                    max_select=group.max_select,
                    display_order=link.display_order,
                    items=[
                        PosSyncAddonItem(
                            id=i.id, addon_group_id=i.addon_group_id, name=i.name,
                            price_delta=i.price_delta, default_selected=i.default_selected,
                            display_order=i.display_order, is_active=i.is_active,
                        )
                        for i in items_by_group.get(group.id, [])
                    ],
                )
            )

        return [
            PosSyncProduct(
                id=p.id,
                category_id=p.category_id,
                product_code=p.product_code,
                name=p.name,
                description=p.description,
                price=prices.get(p.default_variant_id, 0),
                image_path=p.image_path,
                display_order=p.display_order,
                is_active=p.is_active,
                default_variant_id=p.default_variant_id,
                variant_option_groups=vogs_by_product.get(p.id, []),
                addon_groups=addons_by_product.get(p.id, []),
                allow_inventory_tracking=p.allow_inventory_tracking,
            )
            for p in products
        ]

    async def _variants(self, tenant_id, products, branch_id):
        from services.variant_service import VariantService
        from models.variant import Variant
        from schemas.variant import SyncedVariantResponse
        rows = (await self.db.scalars(VariantService(self.db).scoped(tenant_id)
            .where(Variant.product_id.in_([p.id for p in products])))).all()
        products_by_id = {p.id: p for p in products}
        option_ids = {
            UUID(str(option_id))
            for variant in rows
            for option_id in (variant.option_value_ids or [])
        }
        options_by_id = {}
        groups_by_id = {}
        if option_ids:
            options = list((await self.db.scalars(
                select(VariantOption).where(VariantOption.id.in_(option_ids))
            )).all())
            options_by_id = {option.id: option for option in options}
            group_ids = {option.option_group_id for option in options}
            groups = list((await self.db.scalars(
                select(VariantOptionGroup).where(VariantOptionGroup.id.in_(group_ids))
            )).all())
            groups_by_id = {group.id: group for group in groups}
        svc = VariantService(self.db)
        sellability = await svc.compute_sellability(list(rows))
        out = []
        for v in rows:
            stock_by_branch = await svc.stock_snapshot(v)
            stock_here = int(stock_by_branch.get(str(branch_id), 0)) if stock_by_branch else 0
            sellable, sellable_reason = sellability[v.id]
            labels = []
            for option_id in v.option_value_ids or []:
                option = options_by_id.get(UUID(str(option_id)))
                if option is None:
                    continue
                group = groups_by_id.get(option.option_group_id)
                labels.append(f"{group.name}: {option.name}" if group else option.name)
            out.append(SyncedVariantResponse.model_validate(v).model_copy(update={
                'product_name': products_by_id[v.product_id].name,
                'variant_name': ', '.join(labels) if labels else 'Default',
                'sellable': sellable,
                'sellable_reason': sellable_reason,
                'allow_inventory_tracking': products_by_id[v.product_id].allow_inventory_tracking,
                'stock_by_branch': stock_by_branch,
            }))
        return out

    async def _branch_product_ids(self, branch_id: UUID) -> set[UUID]:
        result = await self.db.execute(
            select(ProductBranch.product_id).where(
                ProductBranch.branch_id == branch_id,
                ProductBranch.is_active.is_(True),
            )
        )
        return set(result.scalars().all())

    async def _tax_rates(
        self, tenant_id: UUID, since: datetime | None
    ) -> list[PosSyncTaxRate]:
        stmt = select(TaxRate).where(
            TaxRate.tenant_id == tenant_id,
            TaxRate.deleted_at.is_(None),
        )
        if since:
            stmt = stmt.where(TaxRate.updated_at > since)
        result = await self.db.execute(stmt)
        return [
            PosSyncTaxRate(
                id=t.id,
                name=t.name,
                rate=t.rate,
                is_inclusive=t.is_inclusive,
                is_default=t.is_default,
            )
            for t in result.scalars().all()
        ]

    async def _deals(
        self, tenant_id: UUID, branch_id: UUID, since: datetime | None
    ) -> list[PosSyncDeal]:
        stmt = (
            select(Deal)
            .options(selectinload(Deal.items))
            .where(
                Deal.tenant_id == tenant_id,
                Deal.deleted_at.is_(None),
                Deal.is_active.is_(True),
            )
        )
        if since:
            stmt = stmt.where(Deal.updated_at > since)
        result = await self.db.execute(stmt)
        all_deals = result.scalars().all()

        # Branch-specific deal IDs.
        bd_result = await self.db.execute(
            select(BranchDeal.deal_id).where(BranchDeal.branch_id == branch_id)
        )
        branch_deal_ids: set[UUID] = set(bd_result.scalars().all())

        out: list[PosSyncDeal] = []
        for d in all_deals:
            if not d.all_branches and d.id not in branch_deal_ids:
                continue
            out.append(
                PosSyncDeal(
                    id=d.id,
                    name=d.name,
                    description=d.description,
                    deal_code=d.deal_code,
                    fixed_price=d.fixed_price,
                    discount_value=d.discount_value,
                    discount_type=d.discount_type,
                    valid_from=d.valid_from,
                    valid_until=d.valid_until,
                    is_active=d.is_active,
                    items=[
                        PosSyncDealItem(
                            id=i.id,
                            product_id=i.product_id,
                            category_id=i.category_id,
                            quantity=i.quantity,
                            is_free=i.is_free,
                            sort_order=i.sort_order,
                        )
                        for i in d.items
                        if not i.deleted_at
                    ],
                )
            )
        return out

    async def _promotions(
        self, tenant_id: UUID, branch_id: UUID, since: datetime | None
    ) -> list[PosSyncPromotion]:
        stmt = select(Promotion).where(
            Promotion.tenant_id == tenant_id,
            Promotion.deleted_at.is_(None),
            Promotion.is_active.is_(True),
        )
        if since:
            stmt = stmt.where(Promotion.updated_at > since)
        result = await self.db.execute(stmt)
        all_promos = result.scalars().all()

        bp_result = await self.db.execute(
            select(BranchPromotion.promotion_id).where(
                BranchPromotion.branch_id == branch_id
            )
        )
        branch_promo_ids: set[UUID] = set(bp_result.scalars().all())

        out: list[PosSyncPromotion] = []
        for p in all_promos:
            if not p.all_branches and p.id not in branch_promo_ids:
                continue
            out.append(
                PosSyncPromotion(
                    id=p.id,
                reward_product_id=p.reward_product_id, reward_category_id=p.reward_category_id,
                reward_quantity=p.reward_quantity, reward_discount_type=p.reward_discount_type,
                reward_discount_value=p.reward_discount_value,
                    name=p.name,
                    promo_code=p.promo_code,
                    type=p.type,
                    discount_value=p.discount_value,
                    trigger_min_qty=p.trigger_min_qty,
                    trigger_min_amount=p.trigger_min_amount,
                    trigger_product_id=p.trigger_product_id,
                    trigger_category_id=p.trigger_category_id,
                    valid_from=p.valid_from,
                    valid_until=p.valid_until,
                    max_uses=p.max_uses,
                    used_count=p.used_count,
                    is_active=p.is_active,
                )
            )
        return out

    async def _business_id(self, branch_id: UUID) -> UUID:
        result = await self.db.execute(
            select(Branch.business_id).where(Branch.id == branch_id)
        )
        return result.scalar_one()

    async def _pos_config(self, tenant_id: UUID) -> str:
        """pos_layout from the tenant's Business Template config (spec Part
        C) — synced to the client so the POS can pick its layout offline,
        defaulting to the side-panel layout when unset (older/incomplete
        template config)."""
        from services.business_policy import load_business_policy

        policy = await load_business_policy(self.db, tenant_id)
        pos_config = policy.get("pos", {}) or {}
        return pos_config.get("layout") or "grid_with_variant_picker"

    # ──────────────────────────────────────────────────────────
    # Public interface
    # ──────────────────────────────────────────────────────────

    async def full_sync(self, branch_id: UUID, tenant_id: UUID) -> PosSyncResponse:
        """Return a complete branch snapshot for initial device setup."""
        branch = await self._get_branch(branch_id, tenant_id)
        business_id = branch.business_id
        now = datetime.now(timezone.utc)

        business = await self.db.scalar(select(Business).where(Business.id == business_id))
        logo_base64 = _logo_base64(business.logo_path if business else None)

        categories = await self._categories(business_id, since=None)
        products = await self._products(business_id, branch_id, since=None)
        tax_rates = await self._tax_rates(tenant_id, since=None)
        deals = await self._deals(tenant_id, branch_id, since=None)
        promotions = await self._promotions(tenant_id, branch_id, since=None)
        variants = await self._variants(tenant_id, products, branch_id)
        pos_layout = await self._pos_config(tenant_id)

        return PosSyncResponse(
            branch_id=branch_id,
            branch_name=branch.name,
            branch_code=branch.branch_code,
            branch_address=branch.address,
            branch_phone=branch.phone,
            business_name=business.name if business else "",
            receipt_logo_base64=logo_base64,
            receipt_tagline=business.receipt_tagline if business else None,
            receipt_thank_you=business.receipt_thank_you if business else None,
            receipt_terms=business.receipt_terms if business else None,
            currency=business.currency if business else "Rs.",
            low_stock_threshold=business.low_stock_threshold if business else 5,
            synced_at=now,
            categories=categories,
            products=products,
            tax_rates=tax_rates,
            deals=deals,
            promotions=promotions,
            variants=variants,
            pos_layout=pos_layout,
        )

    async def delta_sync(
        self, branch_id: UUID, tenant_id: UUID, since: datetime
    ) -> PosDeltaSyncResponse:
        """Return only records modified after `since`."""
        branch = await self._get_branch(branch_id, tenant_id)
        business_id = branch.business_id
        now = datetime.now(timezone.utc)

        categories = await self._categories(business_id, since=since)
        products = await self._products(business_id, branch_id, since=since)
        tax_rates = await self._tax_rates(tenant_id, since=since)
        deals = await self._deals(tenant_id, branch_id, since=since)
        promotions = await self._promotions(tenant_id, branch_id, since=since)
        variants = await self._variants(tenant_id, await self._products(business_id, branch_id, since=None), branch_id)
        pos_layout = await self._pos_config(tenant_id)
        business = await self.db.scalar(select(Business).where(Business.id == business_id))

        return PosDeltaSyncResponse(
            branch_id=branch_id,
            branch_name=branch.name,
            branch_code=branch.branch_code,
            branch_address=branch.address,
            branch_phone=branch.phone,
            business_name=business.name if business else "",
            receipt_logo_base64=_logo_base64(business.logo_path if business else None),
            receipt_tagline=business.receipt_tagline if business else None,
            receipt_thank_you=business.receipt_thank_you if business else None,
            receipt_terms=business.receipt_terms if business else None,
            low_stock_threshold=business.low_stock_threshold if business else 5,
            since=since,
            synced_at=now,
            categories=categories,
            products=products,
            tax_rates=tax_rates,
            deals=deals,
            promotions=promotions,
            variants=variants,
            pos_layout=pos_layout,
        )


def _logo_base64(logo_path: str | None) -> str | None:
    """Return the configured logo bytes for durable offline POS storage."""
    if not logo_path or not logo_path.startswith("/media/"):
        return None
    media_root = Path(__file__).resolve().parents[1] / "media"
    candidate = (media_root / logo_path.removeprefix("/media/")).resolve()
    try:
        candidate.relative_to(media_root.resolve())
        return base64.b64encode(candidate.read_bytes()).decode("ascii")
    except (ValueError, OSError):
        return None
