# models/business_template.py
#
# Platform-managed preset for a BUSINESS TYPE ("Fast Food", "Electronics
# Wholesale", ...) — drives Variant/Add-on seeding, inventory strictness,
# pricing fields, POS layout, and which SaaS dashboard modules a tenant can
# access (config.modules.hidden — see core/modules.py and
# services/business_policy.py) for every tenant that adopts it (see
# apps/COMPLETE-IMPLEMENTATION-SPEC.md Part C for the config shape).

from __future__ import annotations

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from sqlalchemy import String


class BusinessTemplate(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "business_templates"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False)
