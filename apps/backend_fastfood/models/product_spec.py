# models/product_spec.py
#
# Repeatable key/value specification rows for a product (e.g. Electronics:
# "Screen Size" -> "6.1 inch"). Gated by template.config.product_fields.specs
# (spec G2/Part B) — unused for a Fast Food-style template, never required.

import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class ProductSpec(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "product_specs"

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    spec_key: Mapped[str] = mapped_column(String(100), nullable=False)
    spec_value: Mapped[str] = mapped_column(String(500), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
