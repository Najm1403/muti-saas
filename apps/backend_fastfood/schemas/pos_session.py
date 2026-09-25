# schemas/pos_session.py

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from schemas.common import APIBaseSchema


class SessionOpenRequest(APIBaseSchema):
    opening_cash: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))
    notes: str | None = Field(None, max_length=500)


class SessionCloseRequest(APIBaseSchema):
    closing_cash: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))
    notes: str | None = Field(None, max_length=500)


class SessionResponse(APIBaseSchema):
    id: UUID
    device_id: UUID
    user_id: UUID
    branch_id: UUID
    tenant_id: UUID
    opened_at: datetime
    closed_at: datetime | None
    opening_cash: Decimal
    closing_cash: Decimal | None
    status: str
    notes: str | None
    created_at: datetime
    # YYMMDD + device letter + per-device daily sequence, e.g. "260924A1".
    # None for shifts opened before this field existed (never backfilled).
    shift_number: str | None = None


class SessionSummary(APIBaseSchema):
    """End-of-shift reconciliation figures for one cashier session."""

    sales_count: int
    subtotal_total: Decimal
    discount_total: Decimal
    tax_total: Decimal
    gross_total: Decimal
    total_payments: Decimal
    by_payment_method: dict[str, Decimal]
    # Always carries all five canonical labels (core.payment_methods.PAYMENT_METHODS
    # — Cash / JazzCash / EasyPaisa / Online Transfer / Credit Card), zero-filled,
    # plus any pre-existing free-text method it couldn't map onto one of them.
    cash_sales_total: Decimal
    refunds_count: int
    refund_total: Decimal
    refunds_by_payment_method: dict[str, Decimal]
    cancellations_count: int = 0
    cancellation_total: Decimal = Decimal("0.00")
    cancellations_by_payment_method: dict[str, Decimal] = {}
    net_total: Decimal
    opening_cash: Decimal
    expected_cash: Decimal  # opening_cash + cash receipts - cash refunds


class SessionSummaryResponse(APIBaseSchema):
    """The open session plus its live reconciliation summary."""

    session: SessionResponse
    summary: SessionSummary


class SessionCloseResponse(APIBaseSchema):
    """Returned after a shift is closed — session, summary, and the cash variance."""

    session: SessionResponse
    summary: SessionSummary
    variance: Decimal  # closing_cash - expected_cash


class SessionVarianceItem(APIBaseSchema):
    """One CLOSED shift's cash-reconciliation row for the tenant dashboard's
    Cash Shortages page — the admin-facing view of the same variance a
    cashier already sees on their own device at close time (see
    CashierSessionService._summary/close), never previously visible to
    anyone else."""

    id: UUID
    shift_number: str | None
    branch_id: UUID
    branch_name: str
    device_id: UUID
    device_name: str
    user_id: UUID
    cashier_name: str
    opened_at: datetime
    closed_at: datetime
    opening_cash: Decimal
    closing_cash: Decimal
    expected_cash: Decimal
    variance: Decimal  # closing_cash - expected_cash; negative = shortage
