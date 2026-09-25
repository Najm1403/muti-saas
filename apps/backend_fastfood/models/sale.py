import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import (
    Base,
    SyncMixin,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.branch import Branch
    from models.device import Device
    from models.user import User
    from models.sale_item import SaleItem
    from models.payment import Payment
    from models.promotion import Promotion
    from models.deal import Deal


class Sale(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    SyncMixin,
):
    """
    Represents a completed or recorded sales transaction.

    A sale belongs to a branch and records which POS device created it.

    Example:
        Business: ABC Fast Food
        Branch: Main Branch
        Device: POS-01
        Sale: SAL-000125

    The Sale stores the financial summary of the transaction.
    Individual products are stored in SaleItem.
    Payment information is handled separately by Payment.
    """

    __tablename__ = "sales"
    variant_inventory_reserved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    branch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("branches.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # Branch where the sale was created.

    device_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("devices.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # POS device that created the sale.

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # Cashier who processed this sale.

    sale_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    # Human-readable sale number, e.g. POS01-000125.

    sold_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    # Actual timestamp when the sale was completed on the POS device.
    # Provided by the client — not the same as created_at which is set
    # by the database at insert time (which may be the sync time).

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    # Total of sale items before discount.

    discount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    # Total discount applied to the sale.

    total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    # Final amount payable after discount.

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="COMPLETED",
        index=True,
    )
    # Sale status: PENDING, COMPLETED, CANCELLED, or REFUNDED.

    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    # Tax amount applied to this sale. Default 0 keeps existing sales unchanged.

    tax_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 4),
        nullable=True,
    )
    # Snapshot of the tax rate percentage at time of sale (e.g. 17.0000 for 17%).
    # Stored separately so changing TaxRate later does not alter historical records.

    promotion_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("promotions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Promotion applied to this sale, if any. SET NULL: promotion deletion keeps sale intact.

    deal_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("deals.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Deal applied to this sale, if any.

    order_status: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        index=True,
    )
    # KDS order lifecycle status, e.g. PENDING, PREPARING, READY, SERVED.
    # Null on pre-KDS records. Managed by kitchen staff via future KDS API.

    session_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("cashier_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Cashier shift this sale belongs to, for end-of-shift reconciliation.
    # Nullable so offline sales still insert if the session id is unknown;
    # the shift summary falls back to a device+cashier+time-window match.

    branch: Mapped["Branch"] = relationship(
        "Branch",
        back_populates="sales",
    )

    device: Mapped["Device"] = relationship(
        "Device",
        back_populates="sales",
    )

    user: Mapped["User"] = relationship(
        "User",
    )

    items: Mapped[list["SaleItem"]] = relationship(
        "SaleItem",
        back_populates="sale",
        cascade="all, delete-orphan",
    )

    payments: Mapped[list["Payment"]] = relationship(
        "Payment",
        back_populates="sale",
        cascade="all, delete-orphan",
    )

    promotion: Mapped["Promotion | None"] = relationship("Promotion")
    deal: Mapped["Deal | None"] = relationship("Deal")

    __table_args__ = (
        UniqueConstraint(
            "branch_id",
            "sale_number",
            name="uq_sale_branch_number",
        ),
    )
