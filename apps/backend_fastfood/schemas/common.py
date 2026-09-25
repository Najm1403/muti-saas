# schemas/common.py

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class APIBaseSchema(BaseModel):
    """
    Base Pydantic schema used throughout the API.

    from_attributes=True allows Pydantic to create a schema
    from a SQLAlchemy ORM object.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )


class UUIDResponseSchema(APIBaseSchema):
    """
    Common response structure for UUID-based resources.
    """

    id: UUID


class TimestampResponseSchema(APIBaseSchema):
    """
    Common timestamps returned by the API.
    """

    created_at: datetime
    updated_at: datetime


class SoftDeleteResponseSchema(APIBaseSchema):
    """
    Soft-delete information returned when required.
    """

    deleted_at: datetime | None = None


class SyncResponseSchema(APIBaseSchema):
    """
    Synchronization information returned to offline clients.
    """

    sync_status: str
    synced_at: datetime | None = None
    sync_error: str | None = None


# ─────────────────────────────────────────────
# Generic helpers
# ─────────────────────────────────────────────

from typing import Generic, TypeVar  # noqa: E402

T = TypeVar("T")


class PaginatedResponse(APIBaseSchema, Generic[T]):
    """
    Standard envelope for paginated list endpoints.

    Usage:
        PaginatedResponse[BranchResponse]
    """

    items: list[T]
    total: int
    page: int
    page_size: int
    has_more: bool


class MessageResponse(APIBaseSchema):
    """
    Simple success/failure message response.
    """

    message: str
    success: bool = True