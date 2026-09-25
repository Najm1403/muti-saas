# schemas/user.py

from decimal import Decimal
from uuid import UUID

from pydantic import EmailStr, Field

from schemas.common import (
    APIBaseSchema,
    UUIDResponseSchema,
    TimestampResponseSchema,
)


class UserCreate(APIBaseSchema):
    """
    Data required to create a new user (POS/dashboard login) within a tenant.

    A User can only be created by promoting an existing, active Employee —
    not as a free-standing account — so every login traces back to one HR
    record and full_name always matches it (see UserService.create()). An
    employee already linked to another User is rejected.

    password is accepted in plain text and hashed by the service layer.
    password_hash is never returned in any response.
    """

    employee_id: UUID
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr | None = None
    password: str = Field(..., min_length=6)
    pin: str | None = Field(
        None,
        min_length=4,
        max_length=6,
        pattern=r"^\d+$",
        description="Optional 4-6 digit POS quick sign-in PIN — hashed server-side.",
    )
    photo_url: str | None = Field(None, max_length=500)
    max_discount_percent: Decimal | None = Field(
        None,
        ge=0,
        le=100,
        description="Ceiling on this cashier's manual POS discount, as a "
        "percent of subtotal. Null means uncapped (still requires the "
        "sales.discount permission to give any discount at all).",
    )


class UserUpdate(APIBaseSchema):
    """
    Fields that may be updated on an existing user.
    All fields are optional — supports PATCH semantics.
    username change is allowed by admins; raises 409 if the new username is
    already taken within the tenant.
    """

    username: str | None = Field(None, min_length=3, max_length=100)
    full_name: str | None = Field(None, min_length=1, max_length=150)
    email: EmailStr | None = None
    photo_url: str | None = Field(None, max_length=500)
    is_active: bool | None = None
    max_discount_percent: Decimal | None = Field(
        None,
        ge=0,
        le=100,
        description="Ceiling on this cashier's manual POS discount, as a "
        "percent of subtotal. Send null explicitly to clear back to "
        "uncapped; omit the field entirely to leave it unchanged.",
    )


class UserSetPin(APIBaseSchema):
    """Admin sets/replaces a user's POS quick sign-in PIN."""

    pin: str = Field(..., min_length=4, max_length=6, pattern=r"^\d+$")


class UserResponse(UUIDResponseSchema, TimestampResponseSchema):
    """
    User record returned by the API.
    password_hash / pin_hash are never included.
    """

    tenant_id: UUID
    username: str
    full_name: str
    email: str | None
    is_active: bool
    all_branches: bool = False
    photo_url: str | None = None
    has_pin: bool = False
    max_discount_percent: Decimal | None = None


class UserRoleAssign(APIBaseSchema):
    """
    Request body for assigning a role to a user.
    """

    role_id: UUID


class UserRoleRemove(APIBaseSchema):
    """
    Request body for removing a role from a user.
    """

    role_id: UUID
