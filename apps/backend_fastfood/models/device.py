# app/models/device.py

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import (
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
)

from core.exceptions import ForbiddenError

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.branch import Branch
    from models.sale import Sale


class DeviceStatus(str, enum.Enum):
    """Lifecycle of a POS device."""
    PENDING   = "PENDING"    # created in the dashboard, activation code issued, not yet paired
    ACTIVE    = "ACTIVE"     # activated by a physical device — may operate
    SUSPENDED = "SUSPENDED"  # temporarily blocked — can be reactivated
    REVOKED   = "REVOKED"    # terminal — token permanently rejected, cannot be reactivated


class SuspendScope(str, enum.Enum):
    """Who put a device into SUSPENDED — only the same (or higher) authority can lift it."""
    TENANT   = "TENANT"
    PLATFORM = "PLATFORM"   # a platform (emergency) suspension the tenant cannot lift


class Device(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
):
    __tablename__ = "devices"

    branch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("branches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    device_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    # Auto-generated (POS-XXXXXX). Kept unique within a branch for support/debugging.

    letter: Mapped[str] = mapped_column(
        String(4),
        nullable=False,
    )
    # Auto-assigned at creation: A, B, C, ... per branch (spreadsheet-style —
    # AA, AB, ... beyond Z), permanent for the device's lifetime — assigned
    # from a count of every device ever created at the branch (including
    # soft-deleted ones), so a letter is never reused. Exists so two devices
    # at the same branch can never generate the same sale_number (each POS
    # app folds its own letter into the number it composes offline) and so
    # staff/receipts can plainly tell "Counter A" from "Counter B" — see
    # services/device_service.py::_next_letter().

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    device_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="POS",
    )
    # POS | Kitchen | Display

    status: Mapped[DeviceStatus] = mapped_column(
        Enum(DeviceStatus, name="device_status", native_enum=False),
        nullable=False,
        default=DeviceStatus.PENDING,
        index=True,
    )

    suspended_scope: Mapped[SuspendScope | None] = mapped_column(
        Enum(SuspendScope, name="device_suspend_scope", native_enum=False),
        nullable=True,
    )

    # Updated by the POS app on every successful sync / heartbeat / activation ("last seen").
    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    # One-time 4-digit activation code, stored as a SHA-256 hex digest.
    # Issued when the tenant creates the device; consumed on first activation.
    activation_code_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        default=None,
        index=True,
    )
    activation_code_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    activation_code_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    # Plaintext of the current one-time code — kept only while it is pending use
    # so the dashboard can re-display it ("Show code"). Cleared the moment the
    # code is consumed (activation), or on revoke / reset.
    activation_code: Mapped[str | None] = mapped_column(
        String(6),
        nullable=True,
        default=None,
    )

    activated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    # Reported by the POS app at activation time.
    activated_platform: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None,
    )
    app_version: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        default=None,
    )

    branch: Mapped["Branch"] = relationship(
        "Branch",
        back_populates="devices",
    )
    sales: Mapped[list["Sale"]] = relationship(
        "Sale",
        back_populates="device",
    )

    __table_args__ = (
        UniqueConstraint(
            "branch_id",
            "device_code",
            name="uq_device_branch_code",
        ),
        # Defense in depth alongside services/device_service.py's row lock:
        # a letter is never reused (spreadsheet-style, permanent for the
        # device's lifetime, checked against every device ever created at
        # the branch including soft-deleted ones — see the letter column's
        # own comment), so it must never collide even under a race the
        # application-level lock somehow missed.
        UniqueConstraint(
            "branch_id",
            "letter",
            name="uq_device_branch_letter",
        ),
    )

    # ── Back-compat read-only views ──────────────────────────────────────
    # Existing readers (sale checks, sync page, tests) use is_active / is_activated.

    @hybrid_property
    def is_active(self) -> bool:  # type: ignore[override]
        return self.status == DeviceStatus.ACTIVE

    @is_active.expression  # type: ignore[no-redef]
    def is_active(cls):
        return cls.status == DeviceStatus.ACTIVE

    @hybrid_property
    def is_activated(self) -> bool:  # type: ignore[override]
        return self.activated_at is not None

    @is_activated.expression  # type: ignore[no-redef]
    def is_activated(cls):
        return cls.activated_at.isnot(None)

    @property
    def activation_state(self) -> str:
        """Fine-grained label for the dashboard.

        revoked | suspended | activated | code_expired | not_activated
        """
        if self.status == DeviceStatus.REVOKED:
            return "revoked"
        if self.status == DeviceStatus.SUSPENDED:
            return "suspended"
        if self.status == DeviceStatus.ACTIVE or self.activated_at is not None:
            return "activated"
        # PENDING — distinguish a live code from a stale one
        exp = self.activation_code_expires_at
        if self.activation_code_hash is None or exp is None:
            return "code_expired"
        from datetime import datetime as _dt, timezone as _tz
        if exp < _dt.now(_tz.utc):
            return "code_expired"
        return "not_activated"


def assert_operational(device: "Device") -> None:
    """Raise ForbiddenError unless the device is ACTIVE.

    Used by the online POS endpoints so a suspended/revoked device is locked out
    the next time it reaches the server.
    """
    if device.status == DeviceStatus.REVOKED:
        raise ForbiddenError("This device has been revoked.", code="DEVICE_REVOKED")
    if device.status == DeviceStatus.SUSPENDED:
        raise ForbiddenError("This device is suspended.", code="DEVICE_SUSPENDED")
    if device.status != DeviceStatus.ACTIVE:
        raise ForbiddenError("This device is not activated.", code="DEVICE_NOT_ACTIVE")
