# schemas/pos_auth.py

from uuid import UUID

from pydantic import Field

from schemas.common import APIBaseSchema


class DeviceActivateRequest(APIBaseSchema):
    """One-time activation code the POS app sends on first launch.

    Accepts the code with or without the display space, e.g. "583 291" or "583291".
    """

    activation_code: str = Field(..., min_length=4, max_length=16)
    platform: str | None = Field(None, max_length=50, examples=["android", "windows"])
    app_version: str | None = Field(None, max_length=30)


class DeviceActivateResponse(APIBaseSchema):
    """Everything the first-install screen needs — no follow-up call required."""

    device_token: str
    device_id: UUID
    device_name: str
    device_type: str
    device_letter: str
    branch_id: UUID
    branch_name: str
    business_id: UUID
    business_name: str
    tenant_id: UUID
    currency: str


class CashierLoginRequest(APIBaseSchema):
    """Cashier credentials submitted at the start of a shift."""

    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1)


class CashierLoginResponse(APIBaseSchema):
    """Returned after a successful cashier login."""

    cashier_token: str
    offline_proof: str
    user_id: UUID
    full_name: str
    device_id: UUID
    branch_id: UUID
    tenant_id: UUID


class StaffMember(APIBaseSchema):
    """One active staff member shown on the tablet's staff-picker grid."""

    user_id: UUID
    full_name: str
    designation: str
    photo_url: str | None = None
    has_pin: bool


class StaffPinRequest(APIBaseSchema):
    """PIN sign-in for a staff member chosen from the grid."""

    user_id: UUID
    pin: str = Field(..., min_length=4, max_length=100)
