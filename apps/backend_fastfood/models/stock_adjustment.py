import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, synonym

from db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, SoftDeleteMixin, SyncMixin


class StockAdjustment(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, SyncMixin):
    __tablename__ = "stock_adjustments"

    variant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("variants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    branch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    # Always branch-scoped now — every stock movement is
    # attributed to exactly one branch.
    adjustment_type: Mapped[str] = mapped_column("change_type", String(30), nullable=False)
    quantity_change: Mapped[int | None] = mapped_column("quantity_delta", Integer, nullable=True)
    resulting_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    change_type = synonym("adjustment_type")
    quantity_delta = synonym("quantity_change")
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Client-side timestamps keep same-transaction adjustments strictly ordered
    # for history views, including SQLite-based tests and offline writes.
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), nullable=False)
