# services/activity_service.py
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.audit_log import AuditLog
from models.user import User
from schemas.activity import ActivityLogResponse


class ActivityService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list(
        self,
        tenant_id: UUID,
        user_id: UUID | None = None,
        action: str | None = None,
        module: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ActivityLogResponse]:
        q = (
            select(AuditLog, User.username, User.full_name)
            .outerjoin(User, AuditLog.user_id == User.id)
            .where(AuditLog.tenant_id == tenant_id, AuditLog.deleted_at.is_(None))
        )
        if user_id:
            q = q.where(AuditLog.user_id == user_id)
        if action:
            q = q.where(AuditLog.action == action.upper())
        if module:
            q = q.where(AuditLog.module == module.lower())
        q = q.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)

        rows = await self.db.execute(q)
        result = []
        for log, username, full_name in rows.all():
            result.append(ActivityLogResponse(
                id=log.id,
                action=log.action,
                module=log.module,
                entity_type=log.entity_type,
                entity_id=log.entity_id,
                description=log.description,
                user_id=log.user_id,
                user_name=full_name or username,
                ip_address=log.ip_address,
                created_at=log.created_at,
            ))
        return result
