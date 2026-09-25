# services/branch_stats_service.py

from __future__ import annotations

from datetime import date, datetime, time, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select, case
from sqlalchemy.ext.asyncio import AsyncSession

from models.branch import Branch
from models.device import Device
from models.business import Business
from models.sale import Sale
from schemas.branch import BranchStatsResponse


class BranchStatsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self, tenant_id: UUID) -> list[BranchStatsResponse]:
        # 1. Get all branch IDs for this tenant
        branches_q = await self.db.execute(
            select(Branch)
            .join(Business, Branch.business_id == Business.id)
            .where(
                Business.tenant_id == tenant_id,
                Business.deleted_at.is_(None),
                Branch.deleted_at.is_(None),
            )
            .order_by(Branch.name)
        )
        branches = branches_q.scalars().all()
        if not branches:
            return []
        branch_ids = [b.id for b in branches]
        return await self._assemble(branches, branch_ids)

    async def get_one(self, branch_id: UUID, tenant_id: UUID) -> BranchStatsResponse:
        branch_q = await self.db.execute(
            select(Branch)
            .join(Business, Branch.business_id == Business.id)
            .where(
                Branch.id == branch_id,
                Business.tenant_id == tenant_id,
                Branch.deleted_at.is_(None),
            )
        )
        branch = branch_q.scalar_one_or_none()
        if branch is None:
            from core.exceptions import NotFoundError
            raise NotFoundError("Branch not found.")
        rows = await self._assemble([branch], [branch.id])
        return rows[0]

    async def _assemble(self, branches: list, branch_ids: list) -> list[BranchStatsResponse]:
        today_date = date.today()
        month_start = datetime.combine(today_date.replace(day=1), time.min, tzinfo=timezone.utc)
        today_start = datetime.combine(today_date, time.min, tzinfo=timezone.utc)
        today_end   = datetime.combine(today_date, time.max, tzinfo=timezone.utc)

        # Device aggregates per branch
        dev_q = await self.db.execute(
            select(
                Device.branch_id,
                func.count(Device.id).label("device_count"),
                func.sum(case((Device.is_active.is_(True), 1), else_=0)).label("active_device_count"),
                func.sum(case((Device.is_activated.is_(True), 1), else_=0)).label("activated_device_count"),
                func.max(Device.last_sync_at).label("last_sync_at"),
            )
            .where(Device.branch_id.in_(branch_ids), Device.deleted_at.is_(None))
            .group_by(Device.branch_id)
        )
        dev_stats = {row.branch_id: row for row in dev_q.all()}

        # Today's COMPLETED sales per branch
        today_q = await self.db.execute(
            select(
                Sale.branch_id,
                func.count(Sale.id).label("count"),
                func.coalesce(func.sum(Sale.total), Decimal("0")).label("revenue"),
            )
            .where(
                Sale.branch_id.in_(branch_ids),
                Sale.deleted_at.is_(None),
                Sale.status == "COMPLETED",
                Sale.sold_at >= today_start,
                Sale.sold_at <= today_end,
            )
            .group_by(Sale.branch_id)
        )
        today_stats = {row.branch_id: row for row in today_q.all()}

        # This month's COMPLETED sales per branch
        month_q = await self.db.execute(
            select(
                Sale.branch_id,
                func.count(Sale.id).label("count"),
                func.coalesce(func.sum(Sale.total), Decimal("0")).label("revenue"),
            )
            .where(
                Sale.branch_id.in_(branch_ids),
                Sale.deleted_at.is_(None),
                Sale.status == "COMPLETED",
                Sale.sold_at >= month_start,
            )
            .group_by(Sale.branch_id)
        )
        month_stats = {row.branch_id: row for row in month_q.all()}

        result = []
        for b in branches:
            d = dev_stats.get(b.id)
            t = today_stats.get(b.id)
            m = month_stats.get(b.id)
            result.append(BranchStatsResponse(
                id=b.id,
                business_id=b.business_id,
                name=b.name,
                branch_code=b.branch_code,
                address=b.address,
                phone=b.phone,
                is_active=b.is_active,
                created_at=b.created_at,
                updated_at=b.updated_at,
                device_count=d.device_count if d else 0,
                active_device_count=d.active_device_count if d else 0,
                activated_device_count=d.activated_device_count if d else 0,
                last_sync_at=d.last_sync_at if d else None,
                today_sales_count=t.count if t else 0,
                today_revenue=Decimal(t.revenue) if t else Decimal("0.00"),
                month_sales_count=m.count if m else 0,
                month_revenue=Decimal(m.revenue) if m else Decimal("0.00"),
            ))
        return result
