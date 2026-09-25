# schemas/auth.py

from pydantic import Field

from schemas.common import APIBaseSchema


class LoginRequest(APIBaseSchema):
    """
    Credentials submitted by a user to log in.

    tenant_code identifies which tenant the user belongs to,
    allowing multiple tenants to share the same username.
    """

    tenant_code: str = Field(..., min_length=2, max_length=50)
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1)


class TokenResponse(APIBaseSchema):
    """
    JWT tokens returned after a successful login.
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    # expires_in is in seconds, matching the OAuth2 convention.


class RefreshRequest(APIBaseSchema):
    """
    Refresh token submitted to obtain a new access token.
    """

    refresh_token: str


class ChangePasswordRequest(APIBaseSchema):
    """
    Password change request submitted by an authenticated user.
    """

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6)


class ForgotPasswordRequest(APIBaseSchema):
    """
    Submitted by a user who has forgotten their password.

    TODO: User model needs an `email` field before this can be implemented.
    TODO: An email/SMS provider (SendGrid, Twilio, etc.) must be wired in.
    """

    tenant_code: str = Field(..., min_length=2, max_length=50)
    email: str = Field(..., description="Email address associated with the account.")


class ResetPasswordRequest(APIBaseSchema):
    """
    Submitted to complete the password reset after receiving the OTP/link.

    TODO: User model needs `password_reset_token` and `password_reset_expires_at` columns.
    """

    tenant_code: str = Field(..., min_length=2, max_length=50)
    token: str = Field(..., description="OTP or signed reset token sent to the user.")
    new_password: str = Field(..., min_length=6)


# ------------------------------------------------------------------
# ME RESPONSE — enhanced /auth/me response with tenant context + roles
# ------------------------------------------------------------------

from datetime import datetime
from uuid import UUID


class TenantContext(APIBaseSchema):
    id: UUID
    name: str
    code: str
    is_active: bool


class SubscriptionBanner(APIBaseSchema):
    """Enough for the tenant dashboard's post-login popup to explain billing
    state without a second API call — see api/v1/auth.py::get_me()."""

    status: str  # TRIAL | ACTIVE | PAST_DUE | SUSPENDED | CANCELLED
    expires_at: datetime | None = None
    grace_ends_at: datetime | None = None  # only meaningful while PAST_DUE
    days_overdue: int | None = None        # only set once past expires_at


class MeResponse(APIBaseSchema):
    id: UUID
    username: str
    full_name: str
    email: str | None = None
    is_active: bool
    tenant: TenantContext
    currency: str = "Rs."   # this shop's money display string (from restaurants.currency)
    roles: list[str]       # list of role names this user holds
    permissions: list[str] = []   # effective permission codes; ["*"] for admin/owner/manager
    modules: list[str] = []       # module keys this tenant may use (platform-controlled); all when unrestricted
    business_features: dict[str, bool] = Field(default_factory=dict)  # template capabilities used by shared tenant navigation
    subscription: SubscriptionBanner | None = None
    # A platform admin's free-text notice for this tenant — billing warnings,
    # policy notes, or any other instruction. Shown as a dismissible-per-
    # message popup on dashboard login; None means nothing to show.
    admin_message: str | None = None
    admin_message_set_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
