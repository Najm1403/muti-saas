# models/variant_branch_stock.py
#
# Transactionally-updated CACHE of a quantity-tracked Variant's balance at one
# branch. The StockAdjustment ledger (models/stock_adjustment.py) is the
# source of truth — every write here must be paired, in the same
# transaction, with a StockAdjustment row. Never update stock_quantity
# directly without that paired ledger row (see spec D2).
#
# Replaces the old JSON-blob (Variant.stock_by_branch) approach entirely —
# this is a real, queryable, per-(variant, branch) row.

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class VariantBranchStock(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "variant_branch_stock"

    variant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("variants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    branch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stock_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    __table_args__ = (
        UniqueConstraint("variant_id", "branch_id", name="uq_variant_branch_stock"),
        CheckConstraint("stock_quantity >= 0", name="ck_variant_branch_stock_nonneg"),
    )
