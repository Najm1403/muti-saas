# schemas/audit_log.py

from uuid import UUID

from pydantic import Field

from schemas.common import (
    UUIDResponseSchema,
    TimestampResponseSchema,
)


class AuditLogResponse(UUIDResponseSchema, TimestampResponseSchema):
    """
    Audit log record returned by the API.

    Audit logs are immutable — create-only, no update or delete via API.

    Examples:
        action = "CREATE",  module = "products",  entity_type = "Product"
        action = "LOGIN",   module = "auth"
        action = "CANCEL",  module = "sales",     entity_type = "Sale"
    """

    tenant_id: UUID
    user_id: UUID | None
    action: str
    module: str
    entity_type: str | None
    entity_id: UUID | None
    description: str | None
    ip_address: str | None


class AuditLogFilter(UUIDResponseSchema):
    """
    Query filters for the audit log list endpoint.
    All fields are optional — combine freely.
    """

    user_id: UUID | None = None
    action: str | None = Field(None, max_length=50)
    module: str | None = Field(None, max_length=50)
    entity_type: str | None = Field(None, max_length=100)
    entity_id: UUID | None = None
