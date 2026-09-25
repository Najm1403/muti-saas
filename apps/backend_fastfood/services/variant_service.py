"""Variant creation/validation, and the branch stock ledger+cache (spec D2/D4).

Stock Balance = Sum of StockAdjustment rows for (variant, branch),
mirrored transactionally into VariantBranchStock.stock_quantity as a fast-read cache.

Never mutate VariantBranchStock.stock_quantity directly without a paired
StockAdjustment row in the same transaction — see change_branch_balance().
"""
import logging
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import func, select

from core.exceptions import ConflictError, NotFoundError, ValidationError
from models.branch import Branch
from models.business import Business
from models.category import Category
from models.product import Product
from models.product_branch import ProductBranch
from models.product_variant_option_group import ProductVariantOptionGroup
from models.sale_item import SaleItem
from models.stock_adjustment import StockAdjustment
from models.variant import Variant
from models.variant_branch_stock import VariantBranchStock
from models.variant_option import VariantOption
from services.business_policy import enforce_pricing_policy, enforce_tracking_policy, resolve_and_enforce_tracking

log = logging.getLogger(__name__)

_PRICE_TOLERANCE = Decimal("0.01")


def combination_key(option_ids):
    """Sorted, joined VariantOption ids ONLY — never AddonItem ids (spec A1/D4)."""
    values = sorted(str(UUID(str(value))) for value in option_ids)
    if len(values) != len(set(values)):
        raise ValidationError("An option value may only appear once in a variant.")
    if len(values) > 50:
        raise ValidationError("A variant supports at most 50 selected option values.")
    return ",".join(values)


def aggregate_demand(lines):
    demand = defaultdict(int)
    for variant_id, quantity in lines:
        if type(quantity) is not int or quantity <= 0:
            raise ValidationError("Quantity must be a positive whole integer.")
        demand[variant_id] += quantity
    return demand


class VariantService:
    def __init__(self, db, created_by=None):
        self.db = db
        self.created_by = created_by

    async def audit_time(self, variant_id):
        previous = await self.db.scalar(select(StockAdjustment.created_at).where(
            StockAdjustment.variant_id == variant_id).order_by(StockAdjustment.created_at.desc()).limit(1))
        now = datetime.now(timezone.utc)
        if previous is not None:
            previous = previous.replace(tzinfo=timezone.utc) if previous.tzinfo is None else previous
            now = max(now, previous + timedelta(microseconds=1))
        return now

    def scoped(self, tenant_id):
        return (select(Variant).join(Product, Variant.product_id == Product.id)
                .join(Category, Product.category_id == Category.id)
                .join(Business, Category.business_id == Business.id)
                .where(Business.tenant_id == tenant_id, Variant.deleted_at.is_(None)))

    async def product(self, tenant_id, product_id):
        row = (await self.db.execute(select(Product, Category)
            .join(Category, Product.category_id == Category.id)
            .join(Business, Category.business_id == Business.id)
            .where(Product.id == product_id, Business.tenant_id == tenant_id,
                   Product.deleted_at.is_(None), Category.deleted_at.is_(None), Business.deleted_at.is_(None)))).first()
        if row is None:
            raise NotFoundError("Product not found.")
        return row

    async def get(self, tenant_id, variant_id, lock=False):
        stmt = self.scoped(tenant_id).where(Variant.id == variant_id)
        if lock:
            stmt = stmt.with_for_update(of=Variant).execution_options(populate_existing=True)
        variant = await self.db.scalar(stmt)
        if variant is None:
            raise NotFoundError("Variant not found.")
        return variant

    async def delete(self, tenant_id, variant_id):
        """Soft-deletes a Variant — the safe cleanup path for a SKU that was
        never actually usable (most commonly the zero-option default Variant
        every product gets at creation (spec D1), left permanently unsellable
        once a required Variant Option Group is attached and real combination
        Variants take over — see compute_sellability). Guarded so it can never
        discard real business data: blocked if the variant has ever been sold,
        still carries stock anywhere, or is the product's only remaining
        Variant (every product must always keep at least one, spec D1).
        """
        variant = await self.get(tenant_id, variant_id, lock=True)

        other_variant_exists = await self.db.scalar(select(Variant.id).where(
            Variant.product_id == variant.product_id, Variant.id != variant.id,
            Variant.deleted_at.is_(None)).limit(1))
        if other_variant_exists is None:
            raise ConflictError("Every product must keep at least one variant — this is the last one.")

        ever_sold = await self.db.scalar(select(SaleItem.id).where(SaleItem.variant_id == variant.id).limit(1))
        if ever_sold is not None:
            raise ConflictError("This variant has sale history and can't be deleted — untrack it instead.")

        stock = await self.stock_snapshot(variant)
        if stock and any(qty for qty in stock.values()):
            raise ConflictError("This variant still has stock at one or more branches — clear it to zero before deleting.")

        variant.deleted_at = datetime.now(timezone.utc)
        if variant.is_default:
            product = await self.db.scalar(select(Product).where(Product.id == variant.product_id))
            if product is not None and product.default_variant_id == variant.id:
                # Once real combination Variants exist, default_variant_id's
                # only job (seeding the "simple product" Price field) is
                # already moot — the dashboard locks that field the moment
                # variant_option_group_count > 0, regardless of this pointer.
                product.default_variant_id = None
        await self.db.flush()

    # ================================================================
    # Sellability — a Variant can go stale without being deleted
    # ================================================================

    UNSELLABLE_REASON = (
        "This SKU does not have a selection for every currently-required Variant "
        "Option Group on its product — usually because a group was attached (or "
        "made required) after this variant was created. It cannot be sold, and "
        "adding stock to it will not make it sellable. Go to the product's "
        "Variants section and create a variant with a value chosen for every "
        "required group."
    )

    async def compute_sellability(self, variants: list[Variant]) -> dict[UUID, tuple[bool, str | None]]:
        """
        For each variant, whether its option_value_ids cover every currently-
        required Variant Option Group attached to its product — returns
        {variant_id: (sellable, reason_if_not)}.

        A product's zero-option default variant (spec D1) is sellable only
        for as long as the product has no *required* groups attached. If a
        required group is attached (or an optional one is made required)
        after the variant already exists, that variant is never automatically
        regenerated or deleted — it silently becomes an orphaned, unsellable
        SKU unless this is checked explicitly. This is exactly the gap that
        let stock be added to a SKU that could never actually be sold.

        Only 'specification'-usage groups count toward this — an
        'inventory_component' group's values are never part of a Variant's
        own option_value_ids (see create()), so requiring them here would
        wrongly flag every product using shareable component inventory.
        """
        if not variants:
            return {}

        product_ids = {v.product_id for v in variants}
        links = (await self.db.scalars(select(ProductVariantOptionGroup).where(
            ProductVariantOptionGroup.product_id.in_(product_ids),
            ProductVariantOptionGroup.is_required.is_(True),
            ProductVariantOptionGroup.usage_type == "specification",
        ))).all()
        required_groups_by_product: dict[UUID, set[UUID]] = defaultdict(set)
        for link in links:
            required_groups_by_product[link.product_id].add(link.option_group_id)

        # option_value_ids is a JSON column — its entries deserialize as plain
        # strings, not UUID objects, so every id must be normalized the same
        # way combination_key() does before it can be compared or looked up.
        all_option_ids: set[UUID] = set()
        for v in variants:
            all_option_ids.update(UUID(str(oid)) for oid in (v.option_value_ids or []))
        options = (await self.db.scalars(select(VariantOption).where(
            VariantOption.id.in_(all_option_ids)
        ))).all() if all_option_ids else []
        group_by_option = {o.id: o.option_group_id for o in options}

        result: dict[UUID, tuple[bool, str | None]] = {}
        for v in variants:
            option_ids = [UUID(str(oid)) for oid in (v.option_value_ids or [])]
            covered = {group_by_option[oid] for oid in option_ids if oid in group_by_option}
            required = required_groups_by_product.get(v.product_id, set())
            result[v.id] = (True, None) if required <= covered else (False, self.UNSELLABLE_REASON)
        return result

    # ================================================================
    # Stock ledger + cache (D2) — quantity-tracked variants
    # ================================================================

    async def get_branch_stock_row(self, variant_id, branch_id, lock=False):
        stmt = select(VariantBranchStock).where(
            VariantBranchStock.variant_id == variant_id, VariantBranchStock.branch_id == branch_id)
        if lock:
            stmt = stmt.with_for_update()
        return await self.db.scalar(stmt)

    async def change_branch_balance(self, variant_id, branch_id, change, *, create_row_if_missing=False):
        row = await self.get_branch_stock_row(variant_id, branch_id, lock=True)
        if row is None:
            if not create_row_if_missing:
                raise ValidationError("This variant is not stocked at the selected branch.")
            row = VariantBranchStock(variant_id=variant_id, branch_id=branch_id, stock_quantity=0)
            self.db.add(row)
            await self.db.flush()
        new_quantity = row.stock_quantity + change
        if new_quantity < 0:
            raise ValidationError("Stock cannot become negative.")
        row.stock_quantity = new_quantity
        return new_quantity

    async def stock_snapshot(self, variant, branch_ids: set | None = None):
        """dict[str(branch_id), int] of current live stock for this variant."""
        if not variant.tracks_inventory:
            return None
        stmt = select(VariantBranchStock.branch_id, VariantBranchStock.stock_quantity).where(
            VariantBranchStock.variant_id == variant.id)
        if branch_ids is not None:
            stmt = stmt.where(VariantBranchStock.branch_id.in_(branch_ids))
        rows = await self.db.execute(stmt)
        return {str(bid): qty for bid, qty in rows.all()}

    async def opening_stock_snapshot(self, variant):
        """Most recent 'opening' StockAdjustment resulting_quantity per branch."""
        sub = (select(StockAdjustment.branch_id, func.max(StockAdjustment.created_at).label("mx"))
               .where(StockAdjustment.variant_id == variant.id, StockAdjustment.adjustment_type == "opening")
               .group_by(StockAdjustment.branch_id).subquery())
        rows = await self.db.execute(
            select(StockAdjustment.branch_id, StockAdjustment.resulting_quantity)
            .join(sub, (StockAdjustment.branch_id == sub.c.branch_id) & (StockAdjustment.created_at == sub.c.mx))
            .where(StockAdjustment.variant_id == variant.id, StockAdjustment.adjustment_type == "opening"))
        result = {str(bid): qty for bid, qty in rows.all()}
        return result or None

    # ================================================================
    # Branch-to-branch stock transfer
    # ================================================================

    async def transfer_stock(self, tenant_id, variant_id, from_branch_id, to_branch_id,
                              quantity, note=None):
        """Moves [quantity] of one Variant's stock from one branch to another.

        The exact same function for a 'fixed' product's own stock and an
        'upgradable' product's shared linked-component stock — both are
        ultimately just Variant stock underneath, so there is no separate
        "transfer a component" code path; this operates on variant_id alone,
        never product_id or variant_option_id.

        Both legs of the transfer share one reference_id so the branch
        stock history screen can show them as a single linked event, not
        two coincidental unrelated movements.
        """
        if type(quantity) is not int or quantity <= 0:
            raise ValidationError("Transfer quantity must be a positive whole number.")
        if from_branch_id == to_branch_id:
            raise ValidationError("Source and destination branch must be different.")

        variant = await self.get(tenant_id, variant_id, lock=True)
        reference_id = str(uuid4())
        now = await self.audit_time(variant_id)

        # change_branch_balance() raises ValidationError itself when the
        # source doesn't have enough (or isn't stocked at all) — same
        # "insufficient stock" guard used everywhere else.
        new_source = await self.change_branch_balance(variant_id, from_branch_id, -quantity)
        self.db.add(StockAdjustment(created_by=self.created_by, variant_id=variant_id, branch_id=from_branch_id,
            adjustment_type="transfer_out", quantity_change=-quantity, resulting_quantity=new_source,
            reference_id=reference_id, note=note, created_at=now))
        new_dest = await self.change_branch_balance(
            variant_id, to_branch_id, quantity, create_row_if_missing=True)
        self.db.add(StockAdjustment(created_by=self.created_by, variant_id=variant_id, branch_id=to_branch_id,
            adjustment_type="transfer_in", quantity_change=quantity, resulting_quantity=new_dest,
            reference_id=reference_id, note=note, created_at=now))

        await self.db.flush()
        return variant

    # ================================================================
    # Branch validation
    # ================================================================

    async def _validated_branch_opening(self, tenant_id, product_id, values):
        product, category = await self.product(tenant_id, product_id)
        allowed = select(Branch.id).where(Branch.business_id == category.business_id,
            Branch.deleted_at.is_(None), Branch.is_active.is_(True))
        if not product.all_branches:
            allowed = allowed.join(ProductBranch, ProductBranch.branch_id == Branch.id).where(
                ProductBranch.product_id == product_id, ProductBranch.is_active.is_(True))
        allowed_ids = {str(id) for id in (await self.db.scalars(allowed)).all()}
        given = {str(UUID(str(key))): amount for key, amount in values.items()}
        if not allowed_ids or set(given) != allowed_ids:
            raise ValidationError("Opening stock must specify every selected active branch exactly once.")
        if any(type(value) is not int or value < 0 for value in given.values()):
            raise ValidationError("Branch opening stock must be a non-negative whole number.")
        return given

    # ================================================================
    # Variant creation (D4) — the structural bug fix
    # ================================================================

    async def create(self, tenant_id, product_id, option_ids, *, sale_price, cost_price=None,
                      tracks_inventory=None, opening_stock_by_branch=None):
        product, category = await self.product(tenant_id, product_id)
        tracks_inventory = await resolve_and_enforce_tracking(
            self.db, tenant_id, tracks_inventory, product.allow_inventory_tracking)
        await enforce_pricing_policy(self.db, tenant_id, cost_price)
        if sale_price is None or sale_price < 0:
            raise ValidationError("sale_price is required and must be non-negative.")
        if not tracks_inventory:
            opening_stock_by_branch = None

        await self.db.execute(select(Product.id).where(Product.id == product_id).with_for_update())
        key = combination_key(option_ids)
        existing = await self.db.scalar(select(Variant).where(
            Variant.product_id == product_id, Variant.combination_key == key,
            Variant.deleted_at.is_(None)))
        if existing:
            raise ConflictError("Variant already exists for this option combination.")

        # Attached Variant Option Groups — via the join table, since groups are
        # shared at the Business level (not owned by a single product).
        links = list((await self.db.scalars(select(ProductVariantOptionGroup).where(
            ProductVariantOptionGroup.product_id == product_id))).all())
        group_ids = {l.option_group_id for l in links}
        options = list((await self.db.scalars(select(VariantOption).where(
            VariantOption.id.in_(option_ids), VariantOption.deleted_at.is_(None),
            VariantOption.is_active.is_(True)))).all()) if option_ids else []
        if len(options) != len(option_ids) or any(o.option_group_id not in group_ids for o in options):
            raise ValidationError("Variant option values must belong to this product.")
        for link in links:
            count = sum(o.option_group_id == link.option_group_id for o in options)
            if link.usage_type == "inventory_component":
                # Shared-component values are never baked into a product's
                # own combination — they resolve at sale time from the
                # option's own shared stock instead (see
                # VariantOption.component_product_id). Selecting one here
                # would recreate the exact per-product duplication this
                # model exists to avoid.
                if count > 0:
                    raise ValidationError(
                        "This is a shared inventory component group — it never has combination "
                        "variants. Its values are chosen at sale time, not baked into a SKU.")
                continue
            if count > 1:
                # Structurally can't happen via the schema (one value per group),
                # but guard explicitly — this is the exact bug this system prevents.
                raise ValidationError("Only one value may be selected per Variant Option Group.")
            if link.is_required and count != 1:
                raise ValidationError("A required Variant Option Group must have exactly one value selected.")

        variant = Variant(product_id=product_id, option_value_ids=[str(i) for i in option_ids],
            combination_key=key, sale_price=sale_price, cost_price=cost_price,
            tracks_inventory=tracks_inventory, is_default=(len(option_ids) == 0))
        self.db.add(variant)
        await self.db.flush()

        if tracks_inventory and opening_stock_by_branch:
            validated = await self._validated_branch_opening(tenant_id, product_id, opening_stock_by_branch)
            for branch_id_str, amount in validated.items():
                bid = UUID(branch_id_str)
                self.db.add(VariantBranchStock(variant_id=variant.id, branch_id=bid, stock_quantity=amount))
                await self.db.flush()
                self.db.add(StockAdjustment(created_by=self.created_by, variant_id=variant.id, branch_id=bid,
                    adjustment_type="opening", quantity_change=amount, resulting_quantity=amount,
                    note="Opening stock", created_at=await self.audit_time(variant.id)))
        return variant

    # ================================================================
    # POS checkout support
    # ================================================================

    async def validate_variant_selection(self, tenant_id, items):
        """Confirms each submitted variant_id actually matches the submitted
        product_id + Variant Option snapshot — the client resolves the
        variant (spec F4), the server re-verifies rather than trusting it.

        Also re-verifies unit_price against the variant's current sale_price
        (never trust a client-cached menu price) and confirms the variant
        covers every required Variant Option Group still attached to the
        product — a product can gain a required group after its zero-option
        default Variant was seeded, and that stale default must stop being
        sellable once it does.
        """
        for item in items:
            variant = await self.get(tenant_id, item.variant_id)
            if variant.product_id != item.product_id:
                raise ValidationError("Variant does not belong to the submitted product.")
            submitted_key = combination_key(o.variant_option_id for o in item.options)
            if submitted_key != variant.combination_key:
                raise ValidationError("Submitted options do not match the selected variant.")
            if abs(item.unit_price - variant.sale_price) > _PRICE_TOLERANCE:
                raise ValidationError("This item's price changed. Refresh the menu and try again.")
            await self._check_required_groups(item.product_id, variant)

    async def _check_required_groups(self, product_id, variant):
        # Only 'specification'-usage groups can ever be covered by a
        # Variant's own option_value_ids (see create()) — an
        # 'inventory_component' group's values are chosen at sale time from
        # the option's own shared stock, never baked into this variant, so
        # requiring them here would wrongly block every sale of the product.
        links = list((await self.db.scalars(select(ProductVariantOptionGroup).where(
            ProductVariantOptionGroup.product_id == product_id,
            ProductVariantOptionGroup.is_required.is_(True),
            ProductVariantOptionGroup.usage_type == "specification",
        ))).all())
        if not links:
            return
        required_group_ids = {link.option_group_id for link in links}
        selected_ids = [UUID(str(v)) for v in variant.option_value_ids]
        options = list((await self.db.scalars(select(VariantOption).where(
            VariantOption.id.in_(selected_ids)))).all()) if selected_ids else []
        covered_group_ids = {o.option_group_id for o in options}
        if required_group_ids - covered_group_ids:
            raise ValidationError(
                "This product requires selections for all required option groups.")

    async def validate_stock(self, tenant_id, lines, branch_id=None):
        """lines: iterable of (variant_id, quantity)."""
        demand = aggregate_demand(lines)
        for variant_id, quantity in demand.items():
            variant = await self.get(tenant_id, variant_id)
            product = await self.db.scalar(select(Product).where(Product.id == variant.product_id))
            if not product.allow_inventory_tracking or not variant.tracks_inventory:
                continue
            row = await self.get_branch_stock_row(variant_id, branch_id)
            balance = row.stock_quantity if row else None
            if balance is None or quantity > balance:
                raise ValidationError(f"Insufficient stock for variant {variant_id}.")

    async def deduct(self, tenant_id, lines, sale_id, branch_id=None):
        """lines: list of (variant_id, quantity, sale_item_id)."""
        lines = list(lines)
        await self.db.flush()
        variant_ids = sorted({line[0] for line in lines}, key=str)
        locked = {}
        for variant_id in variant_ids:
            variant = await self.get(tenant_id, variant_id, lock=True)
            product = await self.db.scalar(select(Product).where(Product.id == variant.product_id))
            locked[variant_id] = (variant, product)

        for line in lines:
            variant_id, quantity = line[0], line[1]
            sale_item_id = line[2] if len(line) >= 3 else None
            if type(quantity) is not int or quantity <= 0:
                raise ValidationError("Quantity must be a positive whole integer.")
            variant, product = locked[variant_id]
            tracked = bool(product.allow_inventory_tracking and variant.tracks_inventory)
            if tracked:
                new_balance = await self.change_branch_balance(variant.id, branch_id, -quantity)
                self.db.add(StockAdjustment(created_by=self.created_by, variant_id=variant.id, branch_id=branch_id,
                    adjustment_type="sale", quantity_change=-quantity, resulting_quantity=new_balance,
                    reference_id=str(sale_id), created_at=await self.audit_time(variant.id)))
            # untracked (e.g. unlimited pizza) — no-op, always sellable.
            if sale_item_id is not None:
                sale_item = await self.db.scalar(select(SaleItem).where(
                    SaleItem.id == sale_item_id, SaleItem.sale_id == sale_id))
                if sale_item is not None:
                    sale_item.tracked_at_sale = tracked
                    sale_item.product_tracking_at_sale = product.allow_inventory_tracking
        await self.db.flush()

    async def restore(self, tenant_id, variant_id, quantity, refund_id, *, tracked_at_sale=False,
                       branch_id=None):
        variant = await self.get(tenant_id, variant_id, lock=True)
        product = await self.db.scalar(select(Product).where(Product.id == variant.product_id))
        if not product.allow_inventory_tracking or not variant.tracks_inventory or not tracked_at_sale:
            log.info("untracked variant, restore skipped", extra={"variant_id": str(variant_id), "refund_id": str(refund_id)})
            return
        if type(quantity) is not int or quantity <= 0:
            raise ValidationError("Tracked variant returns require positive whole units.")
        new_balance = await self.change_branch_balance(variant.id, branch_id, quantity, create_row_if_missing=True)
        self.db.add(StockAdjustment(created_by=self.created_by, variant_id=variant.id, branch_id=branch_id,
            adjustment_type="refund", quantity_change=quantity, resulting_quantity=new_balance,
            reference_id=str(refund_id), created_at=await self.audit_time(variant.id)))
        await self.db.flush()

    # ================================================================
    # Tenant dashboard — tracking toggle / manual adjustments
    # ================================================================

    async def set_tracking(self, tenant_id, variant_id, tracked, opening_stock_by_branch=None):
        variant = await self.get(tenant_id, variant_id, lock=True)
        product = await self.db.scalar(select(Product).where(Product.id == variant.product_id))
        if not product.allow_inventory_tracking:
            raise ValidationError("Enable product inventory tracking before editing variant tracking.")
        await enforce_tracking_policy(self.db, tenant_id, tracked)
        if opening_stock_by_branch is not None and (variant.tracks_inventory or not tracked):
            raise ValidationError("Opening stock can only be set when tracking is first enabled.")
        if tracked and not variant.tracks_inventory:
            validated = await self._validated_branch_opening(tenant_id, variant.product_id, opening_stock_by_branch or {})
            for branch_id_str, amount in validated.items():
                bid = UUID(branch_id_str)
                await self.change_branch_balance(variant.id, bid, amount, create_row_if_missing=True)
                self.db.add(StockAdjustment(created_by=self.created_by, variant_id=variant.id, branch_id=bid,
                    adjustment_type="opening", quantity_change=amount, resulting_quantity=amount,
                    note="Opening stock", created_at=await self.audit_time(variant.id)))
        variant.tracks_inventory = tracked
        await self.db.flush()
        return variant

    async def adjust_stock(self, tenant_id, variant_id, adjustment_type, quantity, note=None, branch_id=None):
        variant = await self.get(tenant_id, variant_id, lock=True)
        product = await self.db.scalar(select(Product).where(Product.id == variant.product_id))
        if not product.allow_inventory_tracking or not variant.tracks_inventory:
            raise ValidationError("Only tracked variants can have stock adjustments.")
        if type(quantity) is not int or quantity <= 0:
            raise ValidationError("Adjustment quantity must be a positive whole number.")
        if adjustment_type == "increase":
            change = quantity
        elif adjustment_type == "decrease":
            change = -quantity
        else:
            raise ValidationError("Unknown stock adjustment type.")
        # A missing row does not mean the branch is invalid for this variant —
        # it commonly means the variant was created with a blank/zero opening
        # stock and no row was ever written (see menu.html's opening-stock
        # payload, now fixed to always send zero explicitly). Treat a missing
        # row as an implied zero balance rather than hard-failing "not stocked
        # at the selected branch" — same as set_stock() already does below.
        # A decrease from an implied zero still correctly fails via the
        # negative-balance guard in change_branch_balance(), just with a
        # clearer message ("Stock cannot become negative").
        new_balance = await self.change_branch_balance(
            variant.id, branch_id, change, create_row_if_missing=True)
        self.db.add(StockAdjustment(created_by=self.created_by, variant_id=variant.id, branch_id=branch_id,
            adjustment_type=f"manual_{adjustment_type}", quantity_change=change, resulting_quantity=new_balance,
            note=note, created_at=await self.audit_time(variant.id)))
        await self.db.flush()
        return variant

    async def set_stock(self, tenant_id, variant_id, quantity, note, branch_id=None):
        variant = await self.get(tenant_id, variant_id, lock=True)
        product = await self.db.scalar(select(Product).where(Product.id == variant.product_id))
        if not product.allow_inventory_tracking or not variant.tracks_inventory:
            raise ValidationError("Only tracked variants can have stock adjustments.")
        if type(quantity) is not int or quantity < 0:
            raise ValidationError("Stock must be a non-negative whole number.")
        current = await self.get_branch_stock_row(variant_id, branch_id)
        change = quantity - (current.stock_quantity if current else 0)
        new_balance = await self.change_branch_balance(variant.id, branch_id, change, create_row_if_missing=True)
        self.db.add(StockAdjustment(created_by=self.created_by, variant_id=variant.id, branch_id=branch_id,
            adjustment_type="manual_set", quantity_change=None, resulting_quantity=quantity, note=note,
            created_at=await self.audit_time(variant.id)))
        await self.db.flush()
        return variant

    async def history(self, tenant_id, variant_id, branch_id=None):
        await self.get(tenant_id, variant_id)
        stmt = select(StockAdjustment).where(StockAdjustment.variant_id == variant_id)
        if branch_id is not None:
            stmt = stmt.where(StockAdjustment.branch_id == branch_id)
        return (await self.db.scalars(stmt.order_by(
                StockAdjustment.created_at.desc(), StockAdjustment.id.desc()))).all()
