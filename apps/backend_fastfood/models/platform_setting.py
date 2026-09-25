# models/platform_setting.py
#
# Key/value store for platform-level configuration.
# One row per setting key — no foreign keys, no soft delete.
# Seeded with defaults on first migration; updated via PATCH /api/platform/settings.

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, TimestampMixin


class PlatformSetting(Base, TimestampMixin):
    __tablename__ = "platform_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
