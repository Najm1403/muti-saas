from __future__ import annotations
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from models.audit_log import AuditLog
from schemas.audit_log import AuditLogFilter


class AuditLogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _apply_filters(self, stmt, tenant_id: UUID, filters: AuditLogFilter):
        stmt = stmt.where(AuditLog.tenant_id == tenant_id, AuditLog.deleted_at.is_(None))
        if filters.user_id:
            stmt = stmt.where(AuditLog.user_id == filters.user_id)
        if filters.action:
            stmt = stmt.where(AuditLog.action == filters.action)
        if filters.module:
            stmt = stmt.where(AuditLog.module == filters.module)
        if filters.entity_type:
            stmt = stmt.where(AuditLog.entity_type == filters.entity_type)
        if filters.entity_id:
            stmt = stmt.where(AuditLog.entity_id == filters.entity_id)
        return stmt

    async def create(
        self,
        tenant_id: UUID,
        action: str,
        module: str,
        user_id: UUID | None = None,
        entity_type: str | None = None,
        entity_id: UUID | None = None,
        description: str | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        log = AuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            module=module,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            ip_address=ip_address,
        )
        self.db.add(log)
        await self.db.flush()
        await self.db.refresh(log)
        return log

    async def list(
        self,
        tenant_id: UUID,
        filters: AuditLogFilter,
        skip: int = 0,
        limit: int = 50,
    ) -> list[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
        stmt = self._apply_filters(stmt, tenant_id, filters)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count(self, tenant_id: UUID, filters: AuditLogFilter) -> int:
        stmt = select(func.count()).select_from(AuditLog)
        stmt = self._apply_filters(stmt, tenant_id, filters)
        result = await self.db.execute(stmt)
        return result.scalar_one()
