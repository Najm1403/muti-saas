# services/pos_sale_service.py
#
# POS-specific sale creation service.
# Accepts a PosSaleCreate where branch_id/device_id/user_id come from the
# cashier JWT. Persists Sale + SaleItems + SaleItemOptions + SaleItemAddons +
# Payments atomically. Returns a PosReceiptResponse ready to be rendered by
# the Flutter app.
#
# Add-on pricing is always re-verified server-side against AddonItem —
# a tampered client payload could otherwise submit price_delta: 0 for a
# paid topping (spec D7).

from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ConflictError, NotFoundError, ValidationError
from models.addon_item import AddonItem
from models.branch import Branch
from models.business import Business
from models.payment import Payment
from models.sale import Sale
from models.sale_item import SaleItem
from models.sale_item_addon import SaleItemAddon
from models.sale_item_option import SaleItemOption
from models.user import User
from schemas.pos_sale import (
    PosSaleCreate,
    PosReceiptAddon,
    PosReceiptItem,
    PosReceiptOption,
    PosReceiptPayment,
    PosReceiptResponse,
)

_TOLERANCE = Decimal("0.01")


class PosSaleService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _receipt_branding(self, branch_id: UUID) -> dict:
        row = (await self.db.execute(
            select(Branch, Business)
            .join(Business, Branch.business_id == Business.id)
            .where(Branch.id == branch_id)
        )).one_or_none()
        if row is None:
            return {}
        branch, business = row
        from services.pos_sync_service import _logo_base64
        return {
            "branch_name": branch.name,
            "branch_code": branch.branch_code,
            "branch_address": branch.address,
            "branch_phone": branch.phone,
            "business_name": business.name,
            "currency": business.currency,
            "receipt_logo_base64": _logo_base64(business.logo_path),
            "receipt_tagline": business.receipt_tagline,
            "receipt_thank_you": business.receipt_thank_you,
            "receipt_terms": business.receipt_terms,
        }

    async def resolve_addon_price_deltas(self, item_data) -> dict:
        # Never trust client-submitted price_delta — always re-fetch from AddonItem.
        # A tampered client payload could otherwise submit price_delta: 0 for a
        # paid topping.
        addon_ids = [a.addon_item_id for a in item_data.addons]
        if not addon_ids:
            return {}
        rows = await self.db.scalars(select(AddonItem).where(AddonItem.id.in_(addon_ids)))
        found = {row.id: row.price_delta for row in rows}
        missing = set(addon_ids) - found.keys()
        if missing:
            raise ValidationError(f"Unknown add-on item(s): {missing}")
        return found

    async def _validate_totals(self, data: PosSaleCreate) -> dict[UUID, dict]:
        """Returns {item_id_index: {addon_item_id: verified_delta}} for reuse when persisting."""
        computed_subtotal = Decimal("0.00")
        verified_deltas: list[dict] = []
        for item in data.items:
            true_deltas = await self.resolve_addon_price_deltas(item)
            verified_deltas.append(true_deltas)
            addon_total = sum(
                (Decimal("0.00") if a.was_removed else true_deltas[a.addon_item_id])
                for a in item.addons
            )
            expected = ((item.unit_price + addon_total) * item.quantity) - item.discount
            if abs(item.total - expected) > _TOLERANCE:
                raise ValidationError(
                    f"Item '{item.product_name}' total mismatch: "
                    f"submitted {item.total}, expected ≈ {expected}."
                )
            computed_subtotal += item.total

        if abs(data.subtotal - computed_subtotal) > _TOLERANCE:
            raise ValidationError(
                f"Sale subtotal mismatch: submitted {data.subtotal}, "
                f"computed {computed_subtotal}."
            )
        expected_total = data.subtotal - data.discount + data.tax_amount
        if abs(data.total - expected_total) > _TOLERANCE:
            raise ValidationError(
                f"Sale total mismatch: submitted {data.total}, "
                f"expected subtotal − discount + tax = {expected_total}."
            )
        return verified_deltas

    async def _validate_component_selections(self, tenant_id: UUID, data: "PosSaleCreate") -> None:
        """
        Laptop Store shareable-inventory model (spec §42/43 — never trust
        client-supplied ids or pairings). Two things are verified:

        1. Every item that claims to be a selected component (all three of
           parent_item_id/satisfies_option_group_id/component_option_id set)
           genuinely resolves: its parent item exists in this same
           submission, the claimed group is really attached to the parent's
           product as 'inventory_component', the claimed option really
           belongs to that group (and to its allow-list, if restricted),
           and the item's own variant_id really is that option's resolved
           shared component Variant — not an arbitrary substitute.
        2. Every 'inventory_component' group marked required on a product in
           this sale has a verified component item satisfying it. This is
           the actual enforcement gap that made "required" meaningless for
           these groups before component selections had anywhere to live.
        """
        from models.product_variant_option_group import ProductVariantOptionGroup
        from models.product_variant_option_allowed import ProductVariantOptionAllowed
        from models.variant_option import VariantOption
        from models.variant_option_group import VariantOptionGroup
        from models.product import Product

        items_by_id = {item.id: item for item in data.items}
        satisfied: set[tuple[UUID, UUID]] = set()  # {(parent_item_id, option_group_id)}
        product_ids = {item.product_id for item in data.items}
        component_product_ids = set((await self.db.scalars(select(
            VariantOption.component_product_id
        ).where(
            VariantOption.component_product_id.in_(product_ids),
            VariantOption.deleted_at.is_(None),
        ))).all())

        for item in data.items:
            fields = (item.parent_item_id, item.satisfies_option_group_id, item.component_option_id)
            if fields == (None, None, None):
                continue
            if None in fields:
                raise ValidationError(
                    f"Item '{item.product_name}': parent_item_id, satisfies_option_group_id and "
                    f"component_option_id must all be set together for a component selection.")

            parent = items_by_id.get(item.parent_item_id)
            if parent is None:
                raise ValidationError(f"Item '{item.product_name}' references a parent item that isn't in this sale.")
            if parent.product_id in component_product_ids:
                raise ValidationError(
                    f"'{parent.product_name}' is an inventory component and cannot have "
                    "component selections of its own."
                )

            # item.satisfies_option_group_id is the *shared* VariantOptionGroup
            # id, not this attachment's own row id: the POS only ever syncs
            # (and echoes back) the shared group's id — see
            # PosSyncService.get_catalog()'s `PosSyncVariantOptionGroup(id=group.id, ...)`
            # — so the per-product attachment must be resolved by
            # (product_id, option_group_id), never by ProductVariantOptionGroup.id.
            group = await self.db.scalar(select(ProductVariantOptionGroup).where(
                ProductVariantOptionGroup.option_group_id == item.satisfies_option_group_id,
                ProductVariantOptionGroup.product_id == parent.product_id,
                ProductVariantOptionGroup.usage_type == "inventory_component",
            ))
            if group is None:
                raise ValidationError(
                    f"Item '{item.product_name}' claims to satisfy a Component Group that isn't attached "
                    f"to '{parent.product_name}' as an inventory component.")

            option = await self.db.scalar(select(VariantOption).where(
                VariantOption.id == item.component_option_id,
                VariantOption.option_group_id == group.option_group_id,
                VariantOption.deleted_at.is_(None),
            ))
            if option is None:
                raise ValidationError(f"Item '{item.product_name}': selected value doesn't belong to that group.")

            allowed_ids = set((await self.db.scalars(select(ProductVariantOptionAllowed.variant_option_id).where(
                ProductVariantOptionAllowed.product_variant_option_group_id == group.id))).all())
            if allowed_ids and option.id not in allowed_ids:
                raise ValidationError(f"'{option.name}' isn't offered on '{parent.product_name}'.")

            if option.component_product_id is None:
                raise ValidationError(f"'{option.name}' isn't set up as a shared inventory item yet.")
            component_product = await self.db.scalar(select(Product).where(Product.id == option.component_product_id))
            if component_product is None or component_product.default_variant_id != item.variant_id:
                raise ValidationError(f"Item '{item.product_name}': variant doesn't match the selected component.")

            satisfied.add((item.parent_item_id, item.satisfies_option_group_id))

        configurable_product_ids = product_ids - component_product_ids
        required_rows = (await self.db.execute(
            select(ProductVariantOptionGroup, VariantOptionGroup.name)
            .join(VariantOptionGroup, ProductVariantOptionGroup.option_group_id == VariantOptionGroup.id)
            .where(
                ProductVariantOptionGroup.product_id.in_(configurable_product_ids),
                ProductVariantOptionGroup.usage_type == "inventory_component",
                ProductVariantOptionGroup.is_required.is_(True),
            )
        )).all()
        required_by_product: dict[UUID, list] = {}
        for group, name in required_rows:
            required_by_product.setdefault(group.product_id, []).append((group, name))

        for item in data.items:
            for group, name in required_by_product.get(item.product_id, []):
                # `satisfied` is keyed by the shared VariantOptionGroup id
                # (see the loop above) — group.id here is this attachment's
                # own row id, a different id space; group.option_group_id is
                # the one that matches.
                if (item.id, group.option_group_id) not in satisfied:
                    raise ValidationError(
                        f"'{item.product_name}' requires a selection for '{name}' — "
                        f"none was included in this sale.")

    async def create(
        self,
        data: PosSaleCreate,
        branch_id: UUID,
        device_id: UUID,
        user_id: UUID,
        tenant_id: UUID,
    ) -> PosReceiptResponse:
        # Manual-discount eligibility (sales.discount) is checked later in
        # this method, inside OfferService.validate() — a Promotion/Deal
        # discount needs no per-user grant, only a discount with neither set
        # does, and that discriminator + the permission check already live
        # there (services/offer_service.py), so there's no separate call here.
        verified_deltas = await self._validate_totals(data)
        paid = sum(p.amount for p in data.payments)
        cash = sum(p.amount for p in data.payments if p.payment_method == "Cash")
        if not data.payments or paid < data.total or paid - data.total > cash:
            raise ValidationError("Payment must cover the total; only cash can produce change.")

        # Serialize receipt creation per branch so concurrent retries cannot double-charge.
        branch = await self.db.scalar(select(Branch).join(Business, Branch.business_id == Business.id)
            .where(Branch.id == branch_id, Business.tenant_id == tenant_id).with_for_update(of=Branch))
        if branch is None:
            raise NotFoundError("Branch not found.")
        # Detect duplicate sale_number (from offline re-submit).
        dup = await self.db.execute(
            select(Sale).where(
                Sale.branch_id == branch_id,
                Sale.sale_number == data.sale_number,
                Sale.deleted_at.is_(None),
            )
        )
        existing = dup.scalar_one_or_none()
        if existing is not None:
            if (data.id == existing.id and existing.device_id == device_id and existing.user_id == user_id
                    and existing.total == data.total and existing.subtotal == data.subtotal
                    and existing.discount == data.discount and existing.tax_amount == data.tax_amount
                    and existing.sold_at == data.sold_at):
                # Check full immutable item and payment snapshots before accepting a retry.
                loaded = await self.db.scalar(select(Sale).where(Sale.id == existing.id).options(
                    selectinload(Sale.items).selectinload(SaleItem.options),
                    selectinload(Sale.items).selectinload(SaleItem.addons),
                    selectinload(Sale.payments)))
                # Compares variant_id and the full addon selection, not just
                # product/price/options — two submissions differing only in
                # which variant was sold at an equal price must never be
                # treated as the same retry.
                def orm_lines(items):
                    return sorted((str(i.variant_id), str(Decimal(str(i.quantity)).normalize()), str(i.unit_price.normalize()),
                        str(i.discount.normalize()), str(i.total.normalize()), str(i.satisfies_option_group_id or ""),
                        str(i.component_option_id or ""),
                        sorted(str(o.variant_option_id) for o in i.options),
                        sorted((str(a.addon_item_id), str(a.price_delta_at_sale.normalize()), a.was_removed) for a in i.addons)) for i in items)
                def data_lines(items):
                    return sorted((str(i.variant_id), str(Decimal(str(i.quantity)).normalize()), str(i.unit_price.normalize()),
                        str(i.discount.normalize()), str(i.total.normalize()), str(i.satisfies_option_group_id or ""),
                        str(i.component_option_id or ""),
                        sorted(str(o.variant_option_id) for o in i.options),
                        sorted((str(a.addon_item_id), str(a.price_delta.normalize()), a.was_removed) for a in i.addons)) for i in items)
                def pays(payments):
                    return sorted((p.payment_method, str((getattr(p, "tendered_amount", None) or p.amount).normalize()), p.reference or "") for p in payments)
                if orm_lines(loaded.items) == data_lines(data.items) and pays(loaded.payments) == pays(data.payments):
                    return await self._build_receipt_response(loaded, branch_id)
            raise ConflictError(
                f"Sale number '{data.sale_number}' already exists for this branch."
            )

        # Ids are assigned up front (not lazily inside the persistence loop
        # below) because component-pairing validation needs every item's
        # final id to resolve parent_item_id references before anything is
        # written — a required-group check that runs after partial writes
        # would leave a half-created sale on failure.
        for item_data in data.items:
            item_data.id = item_data.id or uuid4()

        from services.checkout_validation import validate_catalog
        product_map = await validate_catalog(self.db, data, tenant_id, branch_id)
        from services.variant_service import VariantService
        variant_service = VariantService(self.db, created_by=user_id)
        await variant_service.validate_variant_selection(tenant_id, data.items)
        await self._validate_component_selections(tenant_id, data)
        from services.offer_service import OfferService
        await OfferService(self.db).validate(data, tenant_id, branch_id, user_id)
        from models.tax_rate import TaxRate
        from decimal import ROUND_HALF_UP
        tax = await self.db.scalar(select(TaxRate).where(TaxRate.tenant_id==tenant_id,
            TaxRate.is_default.is_(True), TaxRate.is_active.is_(True), TaxRate.deleted_at.is_(None)).limit(1))
        expected_rate = tax.rate / 100 if tax else Decimal(0)
        # Tax is computed on (subtotal − discount) — already correct for a
        # manually or Promotion/Deal-discounted order, partial or full.
        expected_tax = Decimal(0) if not tax or tax.is_inclusive else ((data.subtotal-data.discount)*expected_rate).quantize(Decimal("0.01"),rounding=ROUND_HALF_UP)
        if (data.tax_rate or 0) != expected_rate or abs(data.tax_amount-expected_tax)>_TOLERANCE:
            raise ValidationError("Tax configuration changed. Refresh the menu before checkout.")
        from models.cashier_session import CashierSession
        from sqlalchemy import or_
        session_query = select(CashierSession).where(
            CashierSession.tenant_id == tenant_id, CashierSession.branch_id == branch_id,
            CashierSession.device_id == device_id, CashierSession.user_id == user_id,
            CashierSession.opened_at <= data.sold_at,
            or_(CashierSession.closed_at.is_(None), CashierSession.closed_at >= data.sold_at))
        if data.session_id:
            session_query = session_query.where(CashierSession.id == data.session_id)
        session = await self.db.scalar(session_query.order_by(CashierSession.opened_at.desc()).limit(1))
        if data.session_id and session is None:
            raise ValidationError("Cashier session does not match this sale.")
        data.session_id = session.id if session else None
        await variant_service.validate_stock(
            tenant_id, [(item.variant_id, item.quantity) for item in data.items], branch_id=branch_id
        )
        station_map: dict[UUID, UUID | None] = {
            pid: p.preparation_station_id for pid, p in product_map.items()
        }

        sale_id = data.id or uuid4()
        sale = Sale(
            id=sale_id,
            branch_id=branch_id,
            device_id=device_id,
            user_id=user_id,
            sale_number=data.sale_number,
            sold_at=data.sold_at,
            subtotal=data.subtotal,
            discount=data.discount,
            total=data.total,
            tax_amount=data.tax_amount,
            tax_rate=data.tax_rate,
            promotion_id=data.promotion_id,
            deal_id=data.deal_id,
            session_id=data.session_id,
            status="COMPLETED",
            variant_inventory_reserved=True,
        )
        self.db.add(sale)

        for item_data, true_deltas in zip(data.items, verified_deltas):
            station_id = station_map.get(item_data.product_id)
            item = SaleItem(
                id=item_data.id,
                sale_id=sale_id,
                product_id=item_data.product_id,
                variant_id=item_data.variant_id,
                product_name=item_data.product_name,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                discount=item_data.discount,
                total=item_data.total,
                preparation_status="PENDING" if station_id else None,
                kitchen_station_id=station_id,
                parent_item_id=item_data.parent_item_id,
                satisfies_option_group_id=item_data.satisfies_option_group_id,
                component_option_id=item_data.component_option_id,
            )
            self.db.add(item)
            for opt_data in item_data.options:
                self.db.add(
                    SaleItemOption(
                        id=opt_data.id or uuid4(),
                        sale_item_id=item.id,
                        variant_option_id=opt_data.variant_option_id,
                        option_name=opt_data.option_name,
                    )
                )
            for addon_data in item_data.addons:
                self.db.add(
                    SaleItemAddon(
                        id=addon_data.id or uuid4(),
                        sale_item_id=item.id,
                        addon_item_id=addon_data.addon_item_id,
                        addon_name=addon_data.addon_name,
                        price_delta_at_sale=true_deltas.get(addon_data.addon_item_id, Decimal("0.00")),
                        was_removed=addon_data.was_removed,
                    )
                )

        remaining_change = max(Decimal(0), paid - data.total)
        for pay_data in data.payments:
            returned = min(remaining_change, pay_data.amount) if pay_data.payment_method == "Cash" else Decimal(0)
            remaining_change -= returned
            self.db.add(
                Payment(
                    sale_id=sale_id,
                    payment_method=pay_data.payment_method,
                    amount=pay_data.amount - returned,
                    tendered_amount=pay_data.amount,
                    reference=pay_data.reference,
                )
            )

        await variant_service.deduct(tenant_id,
            [(item.variant_id, item.quantity, item.id) for item in data.items],
            sale_id, branch_id=branch_id)

        await self.db.commit()
        return await self._receipt(sale_id, branch_id, user_id, data)

    async def get_receipt(
        self, sale_id: UUID, branch_id: UUID, user_id: UUID, tenant_id: UUID
    ) -> PosReceiptResponse:
        """
        Returns the receipt for one of the calling cashier's *own* sales.

        GAP 5 — scoped to user_id so Cashier A cannot pull Cashier B's receipt
        via the regular reprint path. Use get_receipt_by_number for an explicit
        cross-cashier lookup that requires knowing the sale number.

        GAP 2 — tenant_id is now enforced via Branch → Business join, not just
        accepted and silently ignored.
        """
        result = await self.db.execute(
            select(Sale)
            .join(Branch, Sale.branch_id == Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .options(
                selectinload(Sale.items).selectinload(SaleItem.options),
                selectinload(Sale.items).selectinload(SaleItem.addons),
                selectinload(Sale.payments),
            )
            .where(
                Sale.id == sale_id,
                Sale.branch_id == branch_id,
                Sale.user_id == user_id,          # GAP 5: own sales only
                Business.tenant_id == tenant_id,  # GAP 2: tenant enforced
                Sale.deleted_at.is_(None),
            )
        )
        sale = result.scalar_one_or_none()
        if not sale:
            raise NotFoundError("Sale not found.")

        return await self._build_receipt_response(sale, branch_id)

    async def get_receipt_by_number(
        self, sale_number: str, branch_id: UUID, tenant_id: UUID
    ) -> PosReceiptResponse:
        """
        Looks up *any* sale in the branch by its human-readable sale number.

        GAP 5 (explicit cross-cashier reprint) — this is the intentional path
        for Cashier B to print Cashier A's sale. Requiring the exact sale number
        creates an audit trail of deliberate intent; the Flutter UI shows a
        confirmation screen before printing.
        """
        result = await self.db.execute(
            select(Sale)
            .join(Branch, Sale.branch_id == Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .options(
                selectinload(Sale.items).selectinload(SaleItem.options),
                selectinload(Sale.items).selectinload(SaleItem.addons),
                selectinload(Sale.payments),
            )
            .where(
                Sale.sale_number == sale_number,
                Sale.branch_id == branch_id,
                Business.tenant_id == tenant_id,
                Sale.deleted_at.is_(None),
            )
        )
        sale = result.scalar_one_or_none()
        if not sale:
            raise NotFoundError(f"Sale '{sale_number}' not found in this branch.")

        return await self._build_receipt_response(sale, branch_id)

    async def list_recent(self, branch_id: UUID, device_id: UUID, user_id: UUID,
                          tenant_id: UUID, limit: int = 20,
                          date_from=None, date_to=None,
                          session_id: UUID | None = None) -> list[PosReceiptResponse]:
        """Recent bills made by this cashier on this device for cancellation/reprint."""
        stmt = (
            select(Sale)
            .join(Branch, Sale.branch_id == Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .options(
                selectinload(Sale.items).selectinload(SaleItem.options),
                selectinload(Sale.items).selectinload(SaleItem.addons),
                selectinload(Sale.payments),
            )
            .where(
                Sale.branch_id == branch_id, Sale.device_id == device_id,
                Sale.user_id == user_id, Business.tenant_id == tenant_id,
                Sale.deleted_at.is_(None),
            )
            .order_by(Sale.sold_at.desc()).limit(min(max(limit, 1), 200))
        )
        if date_from is not None:
            stmt = stmt.where(Sale.sold_at >= date_from)
        if date_to is not None:
            stmt = stmt.where(Sale.sold_at <= date_to)
        if session_id is not None:
            stmt = stmt.where(Sale.session_id == session_id)
        rows = await self.db.scalars(stmt)
        return [await self._build_receipt_response(sale, branch_id) for sale in rows.all()]

    async def _build_receipt_response(
        self, sale: Sale, branch_id: UUID
    ) -> PosReceiptResponse:
        """Shared receipt builder used by both receipt-fetch paths."""
        branding = await self._receipt_branding(branch_id)

        user_result = await self.db.execute(
            select(User.full_name).where(User.id == sale.user_id)
        )
        cashier_name = user_result.scalar_one_or_none() or ""

        total_paid = sum(p.tendered_amount if p.tendered_amount is not None else p.amount for p in sale.payments)
        change = max(Decimal("0.00"), total_paid - sale.total)
        from models.refund import Refund
        from models.refund_item import RefundItem
        from sqlalchemy import func
        returned_rows = await self.db.execute(
            select(RefundItem.sale_item_id, func.coalesce(func.sum(RefundItem.quantity), 0))
            .join(Refund, RefundItem.refund_id == Refund.id)
            .where(Refund.sale_id == sale.id, Refund.status == "COMPLETED",
                   Refund.deleted_at.is_(None))
            .group_by(RefundItem.sale_item_id)
        )
        returned = {item_id: quantity for item_id, quantity in returned_rows.all()}

        return PosReceiptResponse(
            sale_id=sale.id,
            session_id=sale.session_id,
            user_id=sale.user_id,
            sale_number=sale.sale_number,
            status=sale.status,
            sold_at=sale.sold_at,
            **branding,
            cashier_name=cashier_name,
            items=[
                PosReceiptItem(
                    id=i.id,
                    parent_item_id=i.parent_item_id,
                    product_name=i.product_name,
                    quantity=i.quantity,
                    unit_price=i.unit_price,
                    discount=i.discount,
                    total=i.total,
                    returned_quantity=returned.get(i.id, Decimal("0")),
                    options=[PosReceiptOption(option_name=o.option_name) for o in i.options],
                    addons=[
                        PosReceiptAddon(name=a.addon_name, price_delta=a.price_delta_at_sale, was_removed=a.was_removed)
                        for a in i.addons
                    ],
                )
                for i in sale.items
            ],
            subtotal=sale.subtotal,
            discount=sale.discount,
            tax_amount=sale.tax_amount,
            tax_rate=sale.tax_rate,
            total=sale.total,
            payments=[
                PosReceiptPayment(
                    payment_method=p.payment_method,
                    amount=p.tendered_amount if p.tendered_amount is not None else p.amount,
                    reference=p.reference,
                )
                for p in sale.payments
            ],
            change=change,
        )

    async def _receipt(
        self,
        sale_id: UUID,
        branch_id: UUID,
        user_id: UUID,
        data: PosSaleCreate,
    ) -> PosReceiptResponse:
        branding = await self._receipt_branding(branch_id)

        user_result = await self.db.execute(
            select(User.full_name).where(User.id == user_id)
        )
        cashier_name = user_result.scalar_one_or_none() or ""

        total_paid = sum(p.amount for p in data.payments)
        change = max(Decimal("0.00"), total_paid - data.total)

        return PosReceiptResponse(
            sale_id=sale_id,
            session_id=data.session_id,
            user_id=user_id,
            sale_number=data.sale_number,
            sold_at=data.sold_at,
            **branding,
            cashier_name=cashier_name,
            items=[
                PosReceiptItem(
                    id=i.id,
                    parent_item_id=i.parent_item_id,
                    product_name=i.product_name,
                    quantity=i.quantity,
                    unit_price=i.unit_price,
                    discount=i.discount,
                    total=i.total,
                    options=[PosReceiptOption(option_name=o.option_name) for o in i.options],
                    addons=[
                        PosReceiptAddon(name=a.addon_name, price_delta=a.price_delta, was_removed=a.was_removed)
                        for a in i.addons
                    ],
                )
                for i in data.items
            ],
            subtotal=data.subtotal,
            discount=data.discount,
            tax_amount=data.tax_amount,
            tax_rate=data.tax_rate,
            total=data.total,
            payments=[
                PosReceiptPayment(
                    payment_method=p.payment_method,
                    amount=p.amount,
                    reference=p.reference,
                )
                for p in data.payments
            ],
            change=change,
        )
