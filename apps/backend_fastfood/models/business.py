# models/business.py
#
# Replaces models/restaurant.py. A Tenant has exactly one Business — enforced
# here by the UNIQUE constraint on tenant_id, and on the Python side by
# Tenant.business being a scalar relationship (uselist=False), never a list.
# Do not add multi-business-per-tenant capability (see spec A2).

import uuid

from sqlalchemy import ForeignKey, String, Boolean, Text, Integer
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
    from models.tenant import Tenant
    from models.branch import Branch
    from models.category import Category


class Business(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    SyncMixin,
):
    __tablename__ = "businesses"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        default="Rs.",
        server_default="Rs.",
    )
    # Display string the POS prefixes to money amounts (e.g. "Rs.", "$", "€").
    # Synced to the tablet; the app falls back to "Rs." when absent.

    logo_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    receipt_tagline: Mapped[str | None] = mapped_column(String(80), nullable=True)
    receipt_thank_you: Mapped[str | None] = mapped_column(String(120), nullable=True)
    receipt_terms: Mapped[str | None] = mapped_column(Text, nullable=True)
    low_stock_threshold: Mapped[int] = mapped_column(
        Integer, nullable=False, default=5, server_default="5"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="business",
    )
    branches: Mapped[list["Branch"]] = relationship(
        "Branch",
        back_populates="business",
        cascade="all, delete-orphan",
    )
    categories: Mapped[list["Category"]] = relationship(
        "Category",
        back_populates="business",
        cascade="all, delete-orphan",
    )
