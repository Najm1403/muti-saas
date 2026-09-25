# models/cashier_session.py

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, UUIDPrimaryKeyMixin, TimestampMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.device import Device
    from models.user import User
    from models.branch import Branch


class CashierSession(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Tracks a cashier's open/closed shift on a specific POS device.

    One session is open per device at a time. The cashier opens with an
    opening cash count and closes with a closing cash count for reconciliation.
    """

    __tablename__ = "cashier_sessions"

    device_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("devices.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    branch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("branches.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    opening_cash: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    closing_cash: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    # OPEN or CLOSED
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="OPEN",
        index=True,
    )

    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    shift_number: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    # Human-readable shift code: YYMMDD + the device's permanent letter (see
    # models/device.py::letter) + a per-device daily sequence starting at 1
    # each day — e.g. "260924A1" for device A's first shift opened on
    # 2026-09-24, "260924A2" for its second that same day. Computed once at
    # open() time (services/cashier_session_service.py) and never recomputed,
    # so it stays stable even if earlier same-day shifts are later altered.
    # Nullable because shifts opened before this field existed have none —
    # never backfilled, since the sequence can't be reconstructed reliably
    # after the fact.

    device: Mapped["Device"] = relationship("Device")
    user: Mapped["User"] = relationship("User")
    branch: Mapped["Branch"] = relationship("Branch")
