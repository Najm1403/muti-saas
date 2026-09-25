import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, JSON, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import (
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    SyncMixin,
)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.sale import Sale
    from models.branch import Branch
    from models.device import Device
    from models.refund_item import RefundItem
    from models.user import User
    from models.cashier_session import CashierSession


class Refund(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    SyncMixin,
):
    """
    Represents a refund issued against a Sale.

    A sale may have one or multiple refunds.

    Supports:
        - Full refunds
        - Partial refunds

    Refund items identify which products were refunded.
    """

    __tablename__ = "refunds"

    sale_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sales.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # Original sale being refunded.

    branch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("branches.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # Branch where the refund was processed.

    device_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("devices.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # POS device that processed the refund.

    refund_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    # Human-readable refund number, e.g. POS01-R000125.

    refunded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    # Actual timestamp when the refund was processed on the POS device.
    # Provided by the client — not the same as created_at (sync time).

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    # Total amount refunded.

    refund_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    # CASH, CARD, BANK, DIGITAL, etc.

    payment_breakdown: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict
    )
    # Exact returned amount per original tender method, including split payments.

    reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    # Optional reason for the refund.

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="COMPLETED",
        index=True,
    )
    # COMPLETED, CANCELLED, etc.

    refund_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="RETURN", index=True
    )
    # RETURN for a later item return, CANCEL for a same-shift full reversal.

    processed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("cashier_sessions.id", ondelete="SET NULL"), nullable=True, index=True
    )

    sale: Mapped["Sale"] = relationship(
        "Sale",
    )

    branch: Mapped["Branch"] = relationship(
        "Branch",
    )

    device: Mapped["Device"] = relationship(
        "Device",
    )

    processed_by: Mapped["User | None"] = relationship("User")
    session: Mapped["CashierSession | None"] = relationship("CashierSession")

    items: Mapped[list["RefundItem"]] = relationship(
        "RefundItem",
        back_populates="refund",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "branch_id",
            "refund_number",
            name="uq_refund_branch_number",
        ),
    )
