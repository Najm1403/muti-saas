# services/tenant_dashboard_service.py

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.branch import Branch
from models.device import Device
from models.business import Business
from models.subscription import Subscription, SubscriptionStatus
from models.plan import Plan
from models.sale import Sale
from models.tenant import Tenant
from models.user import User
from models.product import Product
from models.variant import Variant
from models.variant_branch_stock import VariantBranchStock
from models.product_branch import ProductBranch
from models.category import Category
from schemas.dashboard import TenantDashboardStats


class TenantDashboardService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_stats(self, tenant_id: UUID) -> TenantDashboardStats:
        now = datetime.now(timezone.utc)

        # Tenant info
        tenant_result = await self.db.execute(
            select(Tenant).where(Tenant.id == tenant_id, Tenant.deleted_at.is_(None))
        )
        tenant = tenant_result.scalar_one_or_none()

        # Business (needed to scope branches)
        biz_result = await self.db.execute(
            select(Business).where(Business.tenant_id == tenant_id, Business.deleted_at.is_(None))
            .limit(1)
        )
        business = biz_result.scalar_one_or_none()
        business_id = business.id if business else None

        # Branches
        branch_q = select(Branch).where(Branch.deleted_at.is_(None))
        if business_id:
            branch_q = branch_q.where(Branch.business_id == business_id)
        else:
            branch_q = branch_q.where(False)  # no business → no branches
        branches_result = await self.db.execute(branch_q)
        branches = branches_result.scalars().all()
        branch_count = len(branches)
        active_branch_count = sum(1 for b in branches if b.is_active)
        branch_ids = [b.id for b in branches]

        # Devices
        if branch_ids:
            devices_result = await self.db.execute(
                select(Device).where(Device.branch_id.in_(branch_ids), Device.deleted_at.is_(None))
            )
            devices = devices_result.scalars().all()
        else:
            devices = []
        device_count = len(devices)
        active_device_count = sum(1 for d in devices if d.is_active)

        # Users
        user_count: int = await self.db.scalar(
            select(func.count(User.id)).where(User.tenant_id == tenant_id, User.deleted_at.is_(None))
        ) or 0

        # A low-stock warning is meaningful only for variants whose product
        # and variant tracking switches are both on. Count branch/SKU pairs,
        # since stock and replenishment are branch-scoped.
        low_stock_threshold = business.low_stock_threshold if business else 5
        low_stock_count = 0
        active_branch_ids = {b.id for b in branches if b.is_active}
        if active_branch_ids:
            tracked_rows = (await self.db.execute(
                select(Variant.id, Product.id, Product.all_branches).join(
                    Product, Product.id == Variant.product_id
                ).join(
                    Category, Category.id == Product.category_id
                ).where(
                    Category.business_id == business_id,
                    Category.deleted_at.is_(None),
                    Variant.tracks_inventory.is_(True),
                    Variant.deleted_at.is_(None),
                    Product.allow_inventory_tracking.is_(True),
                    Product.deleted_at.is_(None),
                    Product.is_active.is_(True),
                )
            )).all()
            product_ids = {row[1] for row in tracked_rows}
            assignments: dict[UUID, set[UUID]] = {}
            if product_ids:
                for product_id, branch_id in (await self.db.execute(
                    select(ProductBranch.product_id, ProductBranch.branch_id).where(
                        ProductBranch.product_id.in_(product_ids),
                        ProductBranch.branch_id.in_(active_branch_ids),
                        ProductBranch.is_active.is_(True),
                    )
                )).all():
                    assignments.setdefault(product_id, set()).add(branch_id)
            stock = {
                (variant_id, branch_id): quantity
                for variant_id, branch_id, quantity in (await self.db.execute(
                    select(
                        VariantBranchStock.variant_id,
                        VariantBranchStock.branch_id,
                        VariantBranchStock.stock_quantity,
                    ).where(VariantBranchStock.branch_id.in_(active_branch_ids))
                )).all()
            }
            for variant_id, product_id, all_branches in tracked_rows:
                eligible = active_branch_ids if all_branches else assignments.get(product_id, set())
                low_stock_count += sum(
                    1 for branch_id in eligible
                    if stock.get((variant_id, branch_id), 0) <= low_stock_threshold
                )

        # Today's and this month's sales
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        today_sales = Decimal("0")
        today_count = 0
        month_sales = Decimal("0")
        month_count = 0

        if branch_ids:
            sales_result = await self.db.execute(
                select(Sale).where(
                    Sale.branch_id.in_(branch_ids),
                    Sale.deleted_at.is_(None),
                    Sale.status == "COMPLETED",
                    Sale.created_at >= month_start,
                )
            )
            for sale in sales_result.scalars().all():
                month_sales += Decimal(str(sale.total))
                month_count += 1
                if sale.created_at >= today_start:
                    today_sales += Decimal(str(sale.total))
                    today_count += 1

        # Subscription
        sub_result = await self.db.execute(
            select(Subscription, Plan)
            .join(Plan, Subscription.plan_id == Plan.id)
            .where(
                Subscription.tenant_id == tenant_id,
                Subscription.status.in_([
                    SubscriptionStatus.ACTIVE,
                    SubscriptionStatus.TRIAL,
                    SubscriptionStatus.SUSPENDED,
                ])
            )
            .order_by(Subscription.created_at.desc())
            .limit(1)
        )
        sub_row = sub_result.first()
        sub_status = None
        sub_plan = None
        sub_expires_at = None
        trial_ends_at = None
        max_branches = None
        max_devices = None
        max_users = None
        if sub_row:
            sub, plan = sub_row
            sub_status = sub.status.value
            sub_plan = plan.name
            sub_expires_at = sub.expires_at
            trial_ends_at = sub.trial_ends_at
            max_branches = plan.max_branches
            max_devices = plan.max_devices
            max_users = plan.max_users

        return TenantDashboardStats(
            tenant_id=tenant_id,
            tenant_name=tenant.name if tenant else "",
            tenant_code=tenant.tenant_code if tenant else "",
            tenant_is_active=tenant.is_active if tenant else False,
            branch_count=branch_count,
            active_branch_count=active_branch_count,
            device_count=device_count,
            active_device_count=active_device_count,
            user_count=user_count,
            low_stock_count=low_stock_count,
            low_stock_threshold=low_stock_threshold,
            today_sales_count=today_count,
            today_revenue=today_sales.quantize(Decimal("0.01")),
            month_sales_count=month_count,
            month_revenue=month_sales.quantize(Decimal("0.01")),
            subscription_status=sub_status,
            subscription_plan=sub_plan,
            subscription_expires_at=sub_expires_at,
            trial_ends_at=trial_ends_at,
            max_branches=max_branches,
            max_devices=max_devices,
            max_users=max_users,
        )
