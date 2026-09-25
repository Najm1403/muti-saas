# services/inventory_report_service.py
#
# Read-only, tenant-wide inventory reports. Unlike VariantService.history()
# (scoped to one variant at a time), every method here spans the whole
# tenant or one branch — what a printable report needs. Tenant isolation:
# every query is scoped via Business.tenant_id, joined the same way as
# api/v1/variants.py::list_variants() (Variant -> Product -> Category ->
# Business) or, for the ledger tables, via Branch -> Business.

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from models.branch import Branch
from models.business import Business
from models.category import Category
from models.product import Product
from models.stock_adjustment import StockAdjustment
from models.user import User
from models.variant import Variant
from models.variant_branch_stock import VariantBranchStock
from models.variant_option import VariantOption
from models.variant_option_group import VariantOptionGroup
from schemas.inventory_report import StockMovementRow, StockReportRow, StockTransferRow

# A stock-in movement for "last restocked" purposes — mirrors the set used
# to decide whether a variant's balance can be trusted as ever-stocked.
_IN_TYPES = ("opening", "transfer_in", "manual_increase")

_MOVEMENT_LABELS = {
    "opening": "Opening stock",
    "transfer_out": "Transfer out",
    "transfer_in": "Transfer in",
    "sale": "Sale",
    "refund": "Refund",
    "manual_increase": "Manual increase",
    "manual_decrease": "Manual decrease",
    "manual_set": "Manual correction",
}


class InventoryReportService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── shared: variant display name ("Product — Option: Value + ...") ────

    async def _display_names(
        self, variants: list[Variant], products: dict[UUID, Product],
    ) -> dict[UUID, str]:
        """variant_id -> display string. Same batch approach as
        api/v1/variants.py::list_variants() (a shared inventory-component
        product is labeled by the option/group that references it), kept
        independent of the router layer rather than imported from it."""
        option_ids = {UUID(str(oid)) for v in variants for oid in (v.option_value_ids or [])}
        option_names: dict[str, str] = {}
        if option_ids:
            rows = (await self.db.execute(
                select(VariantOption, VariantOptionGroup)
                .join(VariantOptionGroup, VariantOption.option_group_id == VariantOptionGroup.id)
                .where(VariantOption.id.in_(option_ids))
            )).all()
            option_names = {str(o.id): f"{g.name}: {o.name}" for o, g in rows}

        product_ids = set(products.keys())
        component_labels: dict[UUID, str] = {}
        if product_ids:
            rows = (await self.db.execute(
                select(VariantOption.component_product_id, VariantOptionGroup.name, VariantOption.name)
                .join(VariantOptionGroup, VariantOption.option_group_id == VariantOptionGroup.id)
                .where(VariantOption.component_product_id.in_(product_ids))
            )).all()
            component_labels = {pid: f"{gname}: {oname}" for pid, gname, oname in rows}

        out: dict[UUID, str] = {}
        for v in variants:
            product = products.get(v.product_id)
            base_name = component_labels.get(v.product_id) or (product.name if product else "Unknown product")
            parts = [option_names.get(str(oid)) for oid in (v.option_value_ids or [])]
            parts = [p for p in parts if p]
            out[v.id] = f"{base_name} — {' + '.join(parts)}" if parts else base_name
        return out

    # ── Stock report: current / in / out / low ─────────────────────────

    async def stock_report(
        self, *, tenant_id: UUID, branch_id: UUID | None = None,
        status: str = "all", q: str | None = None,
    ) -> list[StockReportRow]:
        """status: all | in_stock | out_of_stock | low_stock.

        low_stock includes zero-stock items (quantity <= threshold), the
        same convention variant-inventory.js already uses client-side for
        the live inventory page's Stock filter — kept identical so the two
        never disagree about what counts as "low".
        """
        stmt = (
            select(Variant, Product, Category.name)
            .join(Product, Variant.product_id == Product.id)
            .join(Category, Product.category_id == Category.id)
            .join(Business, Category.business_id == Business.id)
            .where(
                Business.tenant_id == tenant_id,
                Variant.deleted_at.is_(None), Product.deleted_at.is_(None),
                Category.deleted_at.is_(None), Business.deleted_at.is_(None),
                Product.allow_inventory_tracking.is_(True),
                Variant.tracks_inventory.is_(True),
            )
        )
        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where((Product.name.ilike(like)) | (Product.product_code.ilike(like)))
        rows = (await self.db.execute(stmt.order_by(Product.name))).all()
        if not rows:
            return []

        variants = [r[0] for r in rows]
        products = {r[1].id: r[1] for r in rows}
        category_by_product = {r[1].id: r[2] for r in rows}
        variant_ids = [v.id for v in variants]

        threshold = await self.db.scalar(
            select(Business.low_stock_threshold).where(
                Business.tenant_id == tenant_id, Business.deleted_at.is_(None),
            )
        ) or 5

        stock_stmt = select(
            VariantBranchStock.variant_id, func.coalesce(func.sum(VariantBranchStock.stock_quantity), 0),
        ).where(VariantBranchStock.variant_id.in_(variant_ids))
        if branch_id is not None:
            stock_stmt = stock_stmt.where(VariantBranchStock.branch_id == branch_id)
        stock_stmt = stock_stmt.group_by(VariantBranchStock.variant_id)
        stock_by_variant = {vid: int(qty) for vid, qty in (await self.db.execute(stock_stmt)).all()}

        in_stmt = select(
            StockAdjustment.variant_id, func.max(StockAdjustment.created_at),
        ).where(
            StockAdjustment.variant_id.in_(variant_ids),
            StockAdjustment.adjustment_type.in_(_IN_TYPES),
            StockAdjustment.deleted_at.is_(None),
        )
        if branch_id is not None:
            in_stmt = in_stmt.where(StockAdjustment.branch_id == branch_id)
        in_stmt = in_stmt.group_by(StockAdjustment.variant_id)
        last_in_by_variant = {vid: ts for vid, ts in (await self.db.execute(in_stmt)).all()}

        names = await self._display_names(variants, products)

        out: list[StockReportRow] = []
        for v in variants:
            qty = stock_by_variant.get(v.id, 0)
            if status == "in_stock" and qty <= 0:
                continue
            if status == "out_of_stock" and qty != 0:
                continue
            if status == "low_stock" and qty > threshold:
                continue
            product = products[v.product_id]
            out.append(StockReportRow(
                sku=product.product_code, product_name=names[v.id],
                category_name=category_by_product[v.product_id],
                sale_price=v.sale_price, cost_price=v.cost_price,
                current_stock=qty, stock_value=(v.cost_price or Decimal("0")) * qty,
                last_stock_in=last_in_by_variant.get(v.id),
            ))
        return out

    # ── Stock movement ledger ───────────────────────────────────────────

    async def movement_report(
        self, *, tenant_id: UUID, branch_id: UUID | None = None,
        date_from: datetime | None = None, date_to: datetime | None = None,
        movement_type: str | None = None, limit: int = 500,
    ) -> list[StockMovementRow]:
        stmt = (
            select(StockAdjustment, Variant, Product, Branch.name, User.full_name)
            .join(Variant, StockAdjustment.variant_id == Variant.id)
            .join(Product, Variant.product_id == Product.id)
            .join(Branch, StockAdjustment.branch_id == Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .outerjoin(User, StockAdjustment.created_by == User.id)
            .where(Business.tenant_id == tenant_id, StockAdjustment.deleted_at.is_(None))
        )
        if branch_id is not None:
            stmt = stmt.where(StockAdjustment.branch_id == branch_id)
        if date_from is not None:
            stmt = stmt.where(StockAdjustment.created_at >= date_from)
        if date_to is not None:
            stmt = stmt.where(StockAdjustment.created_at <= date_to)
        if movement_type:
            stmt = stmt.where(StockAdjustment.adjustment_type == movement_type)
        stmt = stmt.order_by(StockAdjustment.created_at.desc()).limit(limit)

        rows = (await self.db.execute(stmt)).all()
        if not rows:
            return []
        variants = [r[1] for r in rows]
        products = {r[2].id: r[2] for r in rows}
        names = await self._display_names(variants, products)

        return [
            StockMovementRow(
                date=adj.created_at, sku=product.product_code, product_name=names[variant.id],
                branch_name=branch_name,
                movement_type=_MOVEMENT_LABELS.get(adj.adjustment_type, adj.adjustment_type),
                quantity_change=adj.quantity_change, resulting_quantity=adj.resulting_quantity,
                recorded_by=user_name, note=adj.note,
            )
            for adj, variant, product, branch_name, user_name in rows
        ]

    # ── Branch-to-branch transfer register ──────────────────────────────

    async def transfer_report(
        self, *, tenant_id: UUID, branch_id: UUID | None = None,
        date_from: datetime | None = None, date_to: datetime | None = None,
        limit: int = 500,
    ) -> list[StockTransferRow]:
        """Pairs each transfer's transfer_out/transfer_in rows (same
        reference_id, see VariantService.transfer_stock()) into one line.
        transfer_out is the anchor; its sibling transfer_in is joined by
        reference_id to recover the destination branch."""
        in_branch = aliased(Branch)
        in_adj = aliased(StockAdjustment)

        stmt = (
            select(StockAdjustment, Variant, Product, Branch.name, in_branch.name, User.full_name)
            .join(Variant, StockAdjustment.variant_id == Variant.id)
            .join(Product, Variant.product_id == Product.id)
            .join(Branch, StockAdjustment.branch_id == Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .join(in_adj, (in_adj.reference_id == StockAdjustment.reference_id)
                  & (in_adj.adjustment_type == "transfer_in"))
            .join(in_branch, in_adj.branch_id == in_branch.id)
            .outerjoin(User, StockAdjustment.created_by == User.id)
            .where(
                Business.tenant_id == tenant_id,
                StockAdjustment.adjustment_type == "transfer_out",
                StockAdjustment.deleted_at.is_(None),
            )
        )
        if branch_id is not None:
            stmt = stmt.where((StockAdjustment.branch_id == branch_id) | (in_adj.branch_id == branch_id))
        if date_from is not None:
            stmt = stmt.where(StockAdjustment.created_at >= date_from)
        if date_to is not None:
            stmt = stmt.where(StockAdjustment.created_at <= date_to)
        stmt = stmt.order_by(StockAdjustment.created_at.desc()).limit(limit)

        rows = (await self.db.execute(stmt)).all()
        if not rows:
            return []
        variants = [r[1] for r in rows]
        products = {r[2].id: r[2] for r in rows}
        names = await self._display_names(variants, products)

        return [
            StockTransferRow(
                date=adj.created_at, sku=product.product_code, product_name=names[variant.id],
                from_branch=from_name, to_branch=to_name,
                quantity=abs(adj.quantity_change or 0), recorded_by=user_name, note=adj.note,
            )
            for adj, variant, product, from_name, to_name, user_name in rows
        ]
