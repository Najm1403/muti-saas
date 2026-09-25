# models/product_variant_option_allowed.py
#
# Restricts which of a shared VariantOptionGroup's options actually apply to
# one product's attachment of that group (spec section 22 — "compatibility
# is product-specific": a business-wide RAM group might offer DDR4 and DDR5
# values, but a given laptop only supports DDR4).
#
# No rows for a given ProductVariantOptionGroup means "every option in the
# group is allowed" — this keeps the common case (no restriction needed)
# completely friction-free and requires no backfill for products that don't
# need it; restriction only ever narrows, and only once the admin actually
# adds rows here.

import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ProductVariantOptionAllowed(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "product_variant_option_allowed"

    product_variant_option_group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product_variant_option_groups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    variant_option_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("variant_options.id", ondelete="CASCADE"), nullable=False, index=True
    )

    __table_args__ = (
        UniqueConstraint(
            "product_variant_option_group_id", "variant_option_id",
            name="uq_product_variant_option_allowed",
        ),
    )
