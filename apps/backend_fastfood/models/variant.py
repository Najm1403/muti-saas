# models/variant.py
#
# Composed SKUs. A Variant is the only thing that is ever actually sold or
# stocked — every product always has at least one (its default_variant_id,
# with option_value_ids == [], see spec D1). Stock itself lives in
# VariantBranchStock; this table only defines identity and price.
#
# option_value_ids holds VariantOption ids ONLY, never AddonItem ids — see
# spec A1/D4. If a code path ever lets an AddonItem id reach this field, the
# combinatorial-explosion bug this whole system exists to prevent is back.

import uuid
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, JSON, String, Numeric, text
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, SoftDeleteMixin, SyncMixin


class Variant(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, SyncMixin):
    __tablename__ = "variants"

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    option_value_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    combination_key: Mapped[str] = mapped_column(String(4096), nullable=False)

    sale_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    cost_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    # gated by business_template.config.pricing — see services/business_policy.py
    compare_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    tracks_inventory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        # Partial (not a plain UniqueConstraint) so a soft-deleted Variant
        # never blocks recreating the same option combination later — e.g.
        # removing then re-offering a Color (see VariantService.delete/
        # create). A soft-deleted row keeps its old combination_key forever;
        # only a live one should ever collide.
        Index(
            "uq_variant_combination", "product_id", "combination_key",
            unique=True, postgresql_where=text("deleted_at IS NULL"),
        ),
        CheckConstraint("sale_price >= 0", name="ck_variant_sale_price_nonneg"),
    )
