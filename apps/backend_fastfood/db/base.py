# app/db/base.py

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, UUID, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.
    """
    pass


# ============================================================
# SYNC STATUS
# ============================================================

class SyncStatus(str, enum.Enum):
    """
    Synchronization state of a record.

    PENDING:
        Record exists locally and still needs synchronization.

    SYNCED:
        Record has successfully synchronized with the cloud.

    FAILED:
        Last synchronization attempt failed.
    """

    PENDING = "PENDING"
    SYNCED = "SYNCED"
    FAILED = "FAILED"


# ============================================================
# UUID PRIMARY KEY
# ============================================================

class UUIDPrimaryKeyMixin:
    """
    Provides a UUID primary key to a model.

    UUIDs are generated locally, which is important for
    offline-first Android devices.

    The same UUID can be safely synchronized to PostgreSQL
    later without generating another ID.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


# ============================================================
# TIMESTAMPS
# ============================================================

class TimestampMixin:
    """
    Provides creation and modification timestamps.

    created_at — set once by the database at INSERT time.
                 On offline devices this is the local insert time;
                 on the cloud it is the sync/receive time.

    updated_at — updated by the database on every UPDATE.
                 This is the primary change-detection field for
                 Cloud → Android pull sync:
                   Android sends:  last_synced_at
                   Cloud queries:  WHERE updated_at > last_synced_at
                 Keep this field accurate; do not set it manually.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ============================================================
# SYNC
# ============================================================

class SyncMixin:
    """
    Tracks the operational sync state of a record (Android → Cloud push).

    This is distinct from change detection:
      - updated_at  → used for CHANGE DETECTION (Cloud → Android pull)
      - sync_status → used for OPERATIONAL SYNC STATE (Android → Cloud push)

    Workflow on the Android device:
      1. Record is created locally → sync_status = PENDING
      2. Android pushes the record to the cloud → sync_status = SYNCED
      3. If the push fails        → sync_status = FAILED, sync_error set

    sync_status lives on the Android local DB. The cloud stores it too
    so that a fresh device can reconstruct its sync state after a wipe.

    synced_at  — timestamp of the last successful sync to the cloud.
    sync_error — last error message if sync_status is FAILED.
    """

    sync_status: Mapped[SyncStatus] = mapped_column(
        Enum(
            SyncStatus,
            name="sync_status",
            native_enum=False,
        ),
        nullable=False,
        default=SyncStatus.PENDING,
        index=True,
    )

    synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    sync_error: Mapped[str | None] = mapped_column(
        nullable=True,
    )


# ============================================================
# SOFT DELETE
# ============================================================

class SoftDeleteMixin:
    """
    Provides soft-delete functionality.

    Records are not physically removed from the database.
    Instead, deleted_at is populated.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None