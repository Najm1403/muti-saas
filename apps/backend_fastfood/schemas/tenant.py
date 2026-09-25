# schemas/tenant.py

from datetime import datetime
from uuid import UUID

from pydantic import Field

from schemas.common import (
    APIBaseSchema,
    UUIDResponseSchema,
    TimestampResponseSchema,
)


class TenantCreate(APIBaseSchema):
    """
    Data required to register a new tenant (business account).

    NOTE: the live tenant-creation path is the platform onboarding endpoint
    (schemas/onboarding.py OnboardingCreate), which also creates the Business,
    owner user, and initial Branch in one transaction. This bare schema/route
    is not currently mounted in app/main.py.
    """

    name: str = Field(..., min_length=1, max_length=150)
    tenant_code: str = Field(
        ...,
        min_length=2,
        max_length=50,
        pattern=r"^[a-z0-9_-]+$",
        description="Lowercase letters, digits, hyphens and underscores only.",
    )
    business_template_id: UUID


class TenantUpdate(APIBaseSchema):
    """
    Fields that a super-admin may update on a tenant.
    """

    name: str | None = Field(None, min_length=1, max_length=150)
    is_active: bool | None = None


class TenantResponse(UUIDResponseSchema, TimestampResponseSchema):
    """
    Tenant data returned by the API.
    """

    name: str
    tenant_code: str
    is_active: bool
    admin_message: str | None = None
    admin_message_set_at: datetime | None = None


class TenantAdminMessageRequest(APIBaseSchema):
    """Body for setting the notice shown to a tenant on dashboard login."""

    message: str = Field(..., min_length=1, max_length=2000)
