# schemas/device.py

from datetime import datetime
from uuid import UUID

from pydantic import Field

from models.device import DeviceStatus, SuspendScope
from schemas.common import (
    APIBaseSchema,
    UUIDResponseSchema,
    TimestampResponseSchema,
)


class DeviceCreate(APIBaseSchema):
    """Data the tenant supplies to register a POS device.

    device_code is generated server-side. The response carries a one-time
    activation code the physical device enters to pair itself.
    """

    name: str = Field(..., min_length=1, max_length=150)
    branch_id: UUID
    device_type: str = Field(default="POS", max_length=50, examples=["POS", "Kitchen", "Display"])


class DeviceUpdate(APIBaseSchema):
    """Editable device fields. Lifecycle changes go through the dedicated endpoints."""

    name: str | None = Field(None, min_length=1, max_length=150)
    device_type: str | None = Field(None, max_length=50)


class DeviceResponse(UUIDResponseSchema, TimestampResponseSchema):
    """Device record returned by the API."""

    branch_id: UUID
    device_code: str
    letter: str
    name: str
    device_type: str
    status: DeviceStatus
    suspended_scope: SuspendScope | None = None
    is_active: bool = False          # hybrid: status == ACTIVE
    is_activated: bool = False       # hybrid: activated_at is not None
    activation_state: str = "not_activated"  # revoked|suspended|activated|code_expired|not_activated
    activated_at: datetime | None = None
    revoked_at: datetime | None = None
    activation_code_expires_at: datetime | None = None
    last_sync_at: datetime | None = None
    activated_platform: str | None = None
    app_version: str | None = None


class DeviceCreatedResponse(DeviceResponse):
    """Returned by create / regenerate-code — carries the plain activation code once."""

    activation_code: str
    activation_code_expires_at: datetime


class ActivationCodeView(APIBaseSchema):
    """What the dashboard needs to (re-)show a pending device's activation code.

    `activation_code` is populated only when a code is currently valid. `used`
    means the device is already activated; `expired` means the last code lapsed —
    in both cases the dashboard shows an explanatory message instead of digits.
    """

    device_id: UUID
    status: DeviceStatus
    activation_code: str | None = None
    activation_code_expires_at: datetime | None = None
    expired: bool = False
    used: bool = False
    can_regenerate: bool = True


class DeviceListItem(DeviceResponse):
    """Device enriched with its branch name and a sync-health classification."""

    branch_name: str
    branch_code: str
    sync_status: str  # "healthy" | "stale" | "offline" | "never"


class DeviceSyncResponse(APIBaseSchema):
    """Device enriched with branch name and sync health classification."""
    id: UUID
    branch_id: UUID
    branch_name: str
    branch_code: str
    name: str
    device_code: str
    device_type: str
    status: DeviceStatus
    is_active: bool
    is_activated: bool
    activated_at: datetime | None = None
    last_sync_at: datetime | None = None
    sync_status: str  # "healthy" | "stale" | "offline" | "never"
    created_at: datetime
    updated_at: datetime
