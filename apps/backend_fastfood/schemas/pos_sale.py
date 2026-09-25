# schemas/pos_sale.py
#
# POS-specific sale schemas. Simpler than the generic SaleCreate:
# branch_id, device_id, and user_id are taken from the cashier JWT,
# not from the request body. Payments are included inline for a single
# atomic request from the POS app.
#
# Variant Options (options) are a display/audit snapshot only — no price.
# Add-ons (addons) are priced independently and always re-verified
# server-side against AddonItem.price_delta (spec D7) — client-submitted
# price_delta is never trusted.

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from schemas.units import Units
from pydantic import Field, field_validator

from core.payment_methods import PAYMENT_METHODS, normalise_payment_method
from schemas.common import APIBaseSchema


class PosSaleVariantOptionSnapshot(APIBaseSchema):
    id: UUID | None = Field(None, description="Client-generated UUID for offline sync.")
    variant_option_id: UUID
    option_name: str = Field(..., max_length=100)


class PosSaleAddonSelection(APIBaseSchema):
    id: UUID | None = Field(None, description="Client-generated UUID for offline sync.")
    addon_item_id: UUID
    addon_name: str = Field(..., max_length=100)
    price_delta: Decimal = Decimal("0.00")
    # Client-submitted; server RE-VERIFIES against AddonItem.price_delta (D7).
    was_removed: bool = False


class PosSaleItemCreate(APIBaseSchema):
    id: UUID | None = Field(None, description="Client-generated UUID for offline sync.")
    variant_id: UUID
    product_id: UUID
    product_name: str = Field(..., max_length=150)
    quantity: Units = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=Decimal("0"))
    discount: Decimal = Field(default=Decimal("0.00"), ge=0)
    total: Decimal = Field(..., ge=Decimal("0"))
    options: list[PosSaleVariantOptionSnapshot] = []
    addons: list[PosSaleAddonSelection] = []
    # Laptop Store shareable-inventory model — a selected 'inventory_component'
    # (e.g. a RAM stick) is submitted as its own ordinary item in this same
    # `items` list, tagged back to the base product's item via these three
    # fields, rather than nested inside it. This keeps pricing/stock
    # validation and deduction completely unchanged (each item is still just
    # "one variant, one price") while letting the server verify a required
    # component group was actually fulfilled and letting the receipt group
    # it visually under its parent.
    parent_item_id: UUID | None = Field(
        None, description="This item's id (elsewhere in this same `items` list) if this line is a "
                           "selected component of another item — omit for a normal, standalone item.")
    satisfies_option_group_id: UUID | None = Field(
        None, description="Which of the parent item's attached Component Groups this selection fulfills.")
    component_option_id: UUID | None = Field(
        None, description="Which VariantOption (e.g. '16GB DDR4') this component line represents.")


class PosSalePaymentCreate(APIBaseSchema):
    """payment_method must be one of core.payment_methods.PAYMENT_METHODS —
    Cash / JazzCash / EasyPaisa / Online Transfer / Credit Card — case and
    spacing insensitive, normalised to the canonical label on the way in.

    amount may be zero — a fully-discounted ($0 total) order still records a
    real payment method, just with nothing owed on it. This is safe without
    any per-payment minimum: PosSaleService.create() already requires the
    SUM of all payments to cover the sale's total (paid >= total), which a
    lone $0 payment can only satisfy when the total itself is $0.
    """

    payment_method: str = Field(..., max_length=50, examples=PAYMENT_METHODS)
    amount: Decimal = Field(..., ge=Decimal("0"))
    reference: str | None = Field(None, max_length=150)

    @field_validator("payment_method", mode="before")
    @classmethod
    def _normalise_method(cls, v: str) -> str:
        return normalise_payment_method(v) if isinstance(v, str) else v


class PosSaleCreate(APIBaseSchema):
    """
    A sale submitted by the POS app. branch_id / device_id / user_id are
    taken from the authenticated cashier JWT — the app does not need to send them.
    """

    id: UUID | None = Field(None, description="Client-generated UUID preserved on server.")
    sale_number: str = Field(..., min_length=1, max_length=50)
    sold_at: datetime = Field(..., description="Actual sale time on the POS device.")
    subtotal: Decimal = Field(..., ge=Decimal("0"))
    discount: Decimal = Field(default=Decimal("0.00"), ge=0)
    total: Decimal = Field(..., ge=Decimal("0"))
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_rate: Decimal | None = None
    promotion_id: UUID | None = None
    deal_id: UUID | None = None
    session_id: UUID | None = Field(
        None,
        description="Open cashier session id, so the sale counts toward shift reconciliation.",
    )
    items: list[PosSaleItemCreate] = Field(..., min_length=1)
    payments: list[PosSalePaymentCreate] = []


# ──────────────────────────────────────────────────────────
# Receipt response — structured for the Flutter receipt widget
# ──────────────────────────────────────────────────────────

class PosReceiptOption(APIBaseSchema):
    option_name: str
    price_adjustment: Decimal = Decimal("0.00")


class PosReceiptAddon(APIBaseSchema):
    name: str
    price_delta: Decimal
    was_removed: bool = False


class PosReceiptItem(APIBaseSchema):
    id: UUID | None = None
    parent_item_id: UUID | None = None
    product_name: str
    quantity: Decimal
    unit_price: Decimal
    discount: Decimal
    total: Decimal
    returned_quantity: Decimal = Decimal("0")
    options: list[PosReceiptOption] = []
    addons: list[PosReceiptAddon] = []


class PosReceiptPayment(APIBaseSchema):
    payment_method: str
    amount: Decimal
    reference: str | None


class PosReceiptResponse(APIBaseSchema):
    """Complete receipt data — everything needed to render and print a receipt."""

    sale_id: UUID
    session_id: UUID | None = None
    user_id: UUID
    sale_number: str
    status: str = "COMPLETED"
    sold_at: datetime
    branch_name: str
    branch_code: str = ""
    branch_address: str | None = None
    branch_phone: str | None = None
    business_name: str = ""
    currency: str = "Rs."
    receipt_logo_base64: str | None = None
    receipt_tagline: str | None = None
    receipt_thank_you: str | None = None
    receipt_terms: str | None = None
    cashier_name: str
    items: list[PosReceiptItem] = []
    subtotal: Decimal
    discount: Decimal
    tax_amount: Decimal
    tax_rate: Decimal | None
    total: Decimal
    payments: list[PosReceiptPayment] = []
    change: Decimal
