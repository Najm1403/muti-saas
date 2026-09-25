# schemas/activity.py
from datetime import datetime
from uuid import UUID

from schemas.common import APIBaseSchema


class ActivityLogResponse(APIBaseSchema):
    """Single audit log entry with joined user name."""
    id: UUID
    action: str
    module: str
    entity_type: str | None = None
    entity_id: UUID | None = None
    description: str | None = None
    user_id: UUID | None = None
    user_name: str | None = None
    ip_address: str | None = None
    created_at: datetime
