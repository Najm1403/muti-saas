# services/report_service.py
#
# Platform-level reporting service.
# All methods query across ALL tenants — for use by platform admins only.
#
# Design philosophy:
#   • Fetch raw rows with minimal SQL aggregation for portability (SQLite + PostgreSQL).
#   • Group and aggregate in Python where cross-DB SQL differences would be painful.
#   • Each public method maps to one endpoint in api/platform/reports.py.

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.audit_log import AuditLog
from models.branch import Branch
from models.device import Device
from models.plan import Plan
from models.business import Business
from models.role import Role
from models.subscription import Subscription, SubscriptionStatus, BillingCycle
from models.subscription_payment import SubscriptionPayment
from models.tenant import Tenant
from models.user import User
from models.user_role import UserRole
from schemas.report import (
    ActivitySummary,
    BranchReport,
    BranchTenantItem,
    DeviceReport,
    DeviceTenantItem,
    PlanBreakdownItem,
    PlanPerformanceItem,
    PlatformSummary,
    RevenueMonthItem,
    RevenuePlanItem,
    RevenueReport,
    SubscriptionReport,
    TenantGrowthPoint,
    TenantReport,
    UserReport,
    UserTenantItem,
)

# Devices that have synced within this window are considered "online".
TWO_HOURS = timedelta(seconds=7200)


class ReportService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ================================================================
    # 1. PLATFORM SUMMARY
    # ================================================================

    async def get_summary(self) -> PlatformSummary:
        """Quick KPI card data: tenant / user / device / branch counts + MRR estimate."""

        now = datetime.now(timezone.utc)

        # Tenants (not soft-deleted)
        result = await self.db.execute(
            select(Tenant).where(Tenant.deleted_at.is_(None))
        )
        tenants = result.scalars().all()
        total_tenants  = len(tenants)
        active_tenants = sum(1 for t in tenants if t.is_active)

        # Users (not soft-deleted)
        result = await self.db.execute(
            select(User).where(User.deleted_at.is_(None))
        )
        total_users = len(result.scalars().all())

        # Branches (not soft-deleted)
        result = await self.db.execute(
            select(Branch).where(Branch.deleted_at.is_(None))
        )
        total_branches = len(result.scalars().all())

        # Devices (not soft-deleted, is_active)
        result = await self.db.execute(
            select(Device).where(Device.deleted_at.is_(None), Device.is_active.is_(True))
        )
        total_devices = len(result.scalars().all())

        # MRR from active + trial subscriptions joined to plan price
        result = await self.db.execute(
            select(Subscription, Plan)
            .join(Plan, Subscription.plan_id == Plan.id)
            .where(Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]))
        )
        mrr = Decimal("0")
        for sub, plan in result.all():
            if sub.billing_cycle == BillingCycle.MONTHLY:
                mrr += Decimal(str(plan.price_monthly))
            else:
                mrr += Decimal(str(plan.price_yearly)) / Decimal("12")

        return PlatformSummary(
            total_tenants=total_tenants,
            active_tenants=active_tenants,
            total_users=total_users,
            total_branches=total_branches,
            total_devices=total_devices,
            estimated_mrr=mrr.quantize(Decimal("0.01")),
        )

    # ================================================================
    # 2. TENANT REPORT
    # ================================================================

    async def get_tenant_report(self, days: int = 30) -> TenantReport:
        now = datetime.now(timezone.utc)
        period_start = now - timedelta(days=days)

        # All non-deleted tenants
        result = await self.db.execute(
            select(Tenant).where(Tenant.deleted_at.is_(None))
        )
        tenants = result.scalars().all()

        total = len(tenants)
        new_this_period = sum(
            1 for t in tenants
            if t.created_at and _to_utc(t.created_at) >= period_start
        )
        active = sum(1 for t in tenants if t.is_active)
        suspended = sum(1 for t in tenants if not t.is_active)

        # Subscription status counts (one subscription per tenant — pick latest)
        result = await self.db.execute(select(Subscription))
        all_subs = result.scalars().all()

        # Map tenant_id → most-recent subscription
        tenant_sub: dict[UUID, Subscription] = {}
        for s in all_subs:
            existing = tenant_sub.get(s.tenant_id)
            if existing is None or _to_utc(s.created_at) > _to_utc(existing.created_at):
                tenant_sub[s.tenant_id] = s

        with_trial = sum(
            1 for s in tenant_sub.values() if s.status == SubscriptionStatus.TRIAL
        )
        with_active_sub = sum(
            1 for s in tenant_sub.values() if s.status == SubscriptionStatus.ACTIVE
        )
        cancelled = sum(
            1 for s in tenant_sub.values() if s.status == SubscriptionStatus.CANCELLED
        )

        # Growth — monthly buckets for last 6 months
        growth = _monthly_growth(tenants, months=6)

        return TenantReport(
            total=total,
            new_this_period=new_this_period,
            active=active,
            suspended=suspended,
            with_trial=with_trial,
            with_active_sub=with_active_sub,
            cancelled=cancelled,
            growth=growth,
        )

    # ================================================================
    # 3. SUBSCRIPTION REPORT
    # ================================================================

    async def get_subscription_report(self) -> SubscriptionReport:
        result = await self.db.execute(
            select(Subscription, Plan)
            .join(Plan, Subscription.plan_id == Plan.id)
        )
        rows = result.all()

        counts: dict[SubscriptionStatus, int] = defaultdict(int)
        # plan_id → {name, tenant_count, monthly_value}
        plan_data: dict[UUID, dict] = {}
        mrr = Decimal("0")

        for sub, plan in rows:
            counts[sub.status] += 1

            pid = plan.id
            if pid not in plan_data:
                plan_data[pid] = {
                    "plan_id": pid,
                    "plan_name": plan.name,
                    "tenant_count": 0,
                    "monthly_value": Decimal("0"),
                }

            if sub.status in (SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL):
                plan_data[pid]["tenant_count"] += 1
                if sub.billing_cycle == BillingCycle.MONTHLY:
                    contrib = Decimal(str(plan.price_monthly))
                else:
                    contrib = Decimal(str(plan.price_yearly)) / Decimal("12")
                plan_data[pid]["monthly_value"] += contrib
                mrr += contrib

        active_count = counts[SubscriptionStatus.ACTIVE]
        total_active = active_count or 1  # avoid div/0

        breakdown = [
            PlanBreakdownItem(
                plan_id=v["plan_id"],
                plan_name=v["plan_name"],
                tenant_count=v["tenant_count"],
                monthly_value=v["monthly_value"].quantize(Decimal("0.01")),
                pct_of_active=round(v["tenant_count"] / total_active * 100, 1),
            )
            for v in sorted(plan_data.values(), key=lambda x: x["tenant_count"], reverse=True)
        ]

        arr = (mrr * Decimal("12")).quantize(Decimal("0.01"))

        return SubscriptionReport(
            active=counts[SubscriptionStatus.ACTIVE],
            trial=counts[SubscriptionStatus.TRIAL],
            expired=counts[SubscriptionStatus.EXPIRED],
            suspended=counts[SubscriptionStatus.SUSPENDED],
            cancelled=counts[SubscriptionStatus.CANCELLED],
            plan_breakdown=breakdown,
            estimated_mrr=mrr.quantize(Decimal("0.01")),
            estimated_arr=arr,
        )

    # ================================================================
    # 4. PLAN PERFORMANCE
    # ================================================================

    async def get_plan_performance(self) -> list[PlanPerformanceItem]:
        # All active plans
        result = await self.db.execute(
            select(Plan).where(Plan.deleted_at.is_(None))
        )
        plans = {p.id: p for p in result.scalars().all()}

        # Active + trial subscriptions
        result = await self.db.execute(
            select(Subscription).where(
                Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL])
            )
        )
        subs = result.scalars().all()

        plan_tenants: dict[UUID, set[UUID]] = defaultdict(set)
        plan_mrr: dict[UUID, Decimal] = defaultdict(lambda: Decimal("0"))

        for s in subs:
            plan = plans.get(s.plan_id)
            if plan is None:
                continue
            plan_tenants[s.plan_id].add(s.tenant_id)
            if s.billing_cycle == BillingCycle.MONTHLY:
                plan_mrr[s.plan_id] += Decimal(str(plan.price_monthly))
            else:
                plan_mrr[s.plan_id] += Decimal(str(plan.price_yearly)) / Decimal("12")

        total_tenants = sum(len(v) for v in plan_tenants.values()) or 1

        items = []
        for plan_id, plan in plans.items():
            tc = len(plan_tenants.get(plan_id, set()))
            items.append(
                PlanPerformanceItem(
                    plan_id=plan_id,
                    plan_name=plan.name,
                    tenant_count=tc,
                    pct_of_tenants=round(tc / total_tenants * 100, 1),
                    mrr=plan_mrr.get(plan_id, Decimal("0")).quantize(Decimal("0.01")),
                )
            )

        items.sort(key=lambda x: x.tenant_count, reverse=True)
        return items

    # ================================================================
    # 5. BRANCH REPORT
    # ================================================================

    async def get_branch_report(self) -> BranchReport:
        # Branches (not soft-deleted)
        result = await self.db.execute(
            select(Branch, Business)
            .join(Business, Branch.business_id == Business.id)
            .where(Branch.deleted_at.is_(None), Business.deleted_at.is_(None))
        )
        rows = result.all()

        # Count branches per tenant_id
        tenant_branches: dict[UUID, int] = defaultdict(int)
        for branch, business in rows:
            tenant_branches[business.tenant_id] += 1

        total_branches = sum(tenant_branches.values())

        # Tenant name lookup
        result = await self.db.execute(
            select(Tenant).where(Tenant.deleted_at.is_(None))
        )
        tenants = {t.id: t for t in result.scalars().all()}

        # Active subscription → plan limit per tenant
        result = await self.db.execute(
            select(Subscription, Plan)
            .join(Plan, Subscription.plan_id == Plan.id)
            .where(Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]))
        )
        tenant_plan_limit: dict[UUID, int] = {}
        for sub, plan in result.all():
            # Keep the most-recently-started subscription's limit
            if sub.tenant_id not in tenant_plan_limit:
                tenant_plan_limit[sub.tenant_id] = plan.max_branches

        breakdown = []
        for tid, count in sorted(tenant_branches.items(), key=lambda x: x[1], reverse=True):
            tenant = tenants.get(tid)
            if tenant is None:
                continue
            breakdown.append(
                BranchTenantItem(
                    tenant_id=tid,
                    tenant_name=tenant.name,
                    branch_count=count,
                    plan_limit=tenant_plan_limit.get(tid, -1),
                )
            )

        return BranchReport(total_branches=total_branches, tenant_breakdown=breakdown)

    # ================================================================
    # 6. DEVICE REPORT
    # ================================================================

    async def get_device_report(self) -> DeviceReport:
        now = datetime.now(timezone.utc)
        online_cutoff = now - TWO_HOURS

        # All non-deleted devices with branch → business → tenant chain
        result = await self.db.execute(
            select(Device, Branch, Business)
            .join(Branch, Device.branch_id == Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .where(
                Device.deleted_at.is_(None),
                Branch.deleted_at.is_(None),
                Business.deleted_at.is_(None),
            )
        )
        rows = result.all()

        total = 0
        activated = 0
        never_activated = 0
        online = 0
        offline = 0
        disabled = 0

        # per-tenant: {tenant_id: {total, online, offline}}
        tenant_stats: dict[UUID, dict] = defaultdict(lambda: {"total": 0, "online": 0, "offline": 0})

        for device, branch, business in rows:
            tid = business.tenant_id
            total += 1
            tenant_stats[tid]["total"] += 1

            if not device.is_active:
                disabled += 1
                tenant_stats[tid]["offline"] += 1
                continue

            if device.is_activated:
                activated += 1
                sync_ok = (
                    device.last_sync_at is not None
                    and _to_utc(device.last_sync_at) >= online_cutoff
                )
                if sync_ok:
                    online += 1
                    tenant_stats[tid]["online"] += 1
                else:
                    offline += 1
                    tenant_stats[tid]["offline"] += 1
            else:
                never_activated += 1
                offline += 1
                tenant_stats[tid]["offline"] += 1

        # Tenant name lookup
        result = await self.db.execute(
            select(Tenant).where(Tenant.deleted_at.is_(None))
        )
        tenants = {t.id: t for t in result.scalars().all()}

        breakdown = []
        for tid, stats in sorted(tenant_stats.items(), key=lambda x: x[1]["total"], reverse=True):
            tenant = tenants.get(tid)
            if tenant is None:
                continue
            breakdown.append(
                DeviceTenantItem(
                    tenant_id=tid,
                    tenant_name=tenant.name,
                    total=stats["total"],
                    online=stats["online"],
                    offline=stats["offline"],
                )
            )

        return DeviceReport(
            total=total,
            activated=activated,
            never_activated=never_activated,
            online=online,
            offline=offline,
            disabled=disabled,
            tenant_breakdown=breakdown,
        )

    # ================================================================
    # 7. USER REPORT
    # ================================================================

    async def get_user_report(self) -> UserReport:
        # All non-deleted users
        result = await self.db.execute(
            select(User).where(User.deleted_at.is_(None))
        )
        users = result.scalars().all()

        total = len(users)
        active = sum(1 for u in users if u.is_active)
        disabled = total - active

        # Per-tenant count
        tenant_user_counts: dict[UUID, int] = defaultdict(int)
        for u in users:
            tenant_user_counts[u.tenant_id] += 1

        # Role counts: join UserRole → Role, filter deleted_at IS NULL
        result = await self.db.execute(
            select(UserRole, Role)
            .join(Role, UserRole.role_id == Role.id)
            .where(UserRole.deleted_at.is_(None), Role.deleted_at.is_(None))
        )
        role_rows = result.all()

        owners = 0
        managers = 0
        staff = 0
        for ur, role in role_rows:
            name_lower = role.name.lower()
            if "owner" in name_lower:
                owners += 1
            elif "manager" in name_lower:
                managers += 1
            else:
                staff += 1

        # Tenant name lookup
        result = await self.db.execute(
            select(Tenant).where(Tenant.deleted_at.is_(None))
        )
        tenants = {t.id: t for t in result.scalars().all()}

        breakdown = []
        for tid, count in sorted(tenant_user_counts.items(), key=lambda x: x[1], reverse=True):
            tenant = tenants.get(tid)
            if tenant is None:
                continue
            breakdown.append(
                UserTenantItem(
                    tenant_id=tid,
                    tenant_name=tenant.name,
                    user_count=count,
                )
            )

        return UserReport(
            total=total,
            active=active,
            disabled=disabled,
            owners=owners,
            managers=managers,
            staff=staff,
            tenant_breakdown=breakdown,
        )

    # ================================================================
    # 8. ACTIVITY REPORT
    # ================================================================

    async def get_activity_report(self, days: int = 30) -> ActivitySummary:
        now = datetime.now(timezone.utc)
        period_start = now - timedelta(days=days)

        # Count from source tables for creations (more reliable than audit log)
        # Tenant creations
        result = await self.db.execute(
            select(Tenant).where(
                Tenant.deleted_at.is_(None),
                Tenant.created_at >= period_start,
            )
        )
        tenant_creations = len(result.scalars().all())

        # Device registrations
        result = await self.db.execute(
            select(Device).where(
                Device.deleted_at.is_(None),
                Device.created_at >= period_start,
            )
        )
        device_registrations = len(result.scalars().all())

        # Branch creations
        result = await self.db.execute(
            select(Branch).where(
                Branch.deleted_at.is_(None),
                Branch.created_at >= period_start,
            )
        )
        branch_creations = len(result.scalars().all())

        # User creations
        result = await self.db.execute(
            select(User).where(
                User.deleted_at.is_(None),
                User.created_at >= period_start,
            )
        )
        user_creations = len(result.scalars().all())

        # Logins / failed logins from AuditLog
        result = await self.db.execute(
            select(AuditLog).where(
                AuditLog.created_at >= period_start,
                AuditLog.action.in_(["LOGIN", "FAILED_LOGIN"]),
            )
        )
        audit_rows = result.scalars().all()

        logins = sum(1 for a in audit_rows if a.action == "LOGIN")
        failed_logins = sum(1 for a in audit_rows if a.action == "FAILED_LOGIN")

        return ActivitySummary(
            tenant_creations=tenant_creations,
            device_registrations=device_registrations,
            branch_creations=branch_creations,
            user_creations=user_creations,
            logins=logins,
            failed_logins=failed_logins,
        )

    # ================================================================
    # 9. REVENUE REPORT
    # ================================================================

    async def get_revenue_report(self, days: int = 30) -> RevenueReport:
        now = datetime.now(timezone.utc)

        # Determine month boundaries
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_end = this_month_start
        last_month_start = (this_month_start - timedelta(days=1)).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        # All payments — join to subscription → plan for plan name
        result = await self.db.execute(
            select(SubscriptionPayment, Subscription, Plan)
            .join(Subscription, SubscriptionPayment.subscription_id == Subscription.id)
            .join(Plan, Subscription.plan_id == Plan.id)
        )
        rows = result.all()

        this_month = Decimal("0")
        last_month = Decimal("0")
        by_plan: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        monthly_buckets: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

        # Compute 6-month window
        six_months_ago = now - timedelta(days=183)

        for payment, sub, plan in rows:
            paid_at = _to_utc(payment.paid_at)
            amount = Decimal(str(payment.amount))

            if paid_at >= this_month_start:
                this_month += amount

            if last_month_start <= paid_at < last_month_end:
                last_month += amount

            if paid_at >= six_months_ago:
                bucket = f"{paid_at.year}-{paid_at.month:02d}"
                monthly_buckets[bucket] += amount

            # Always accumulate by_plan (all time — or filter to days if preferred)
            by_plan[plan.name] += amount

        # Growth percentage
        growth_pct: float | None = None
        if last_month > Decimal("0"):
            growth_pct = round(
                float((this_month - last_month) / last_month * 100), 1
            )
        elif this_month > Decimal("0"):
            growth_pct = 100.0

        # Build last-6-months trend (ensure all months present, sorted)
        trend_labels = _last_n_month_labels(6, now)
        monthly_trend = [
            RevenueMonthItem(
                month=label,
                amount=monthly_buckets.get(label, Decimal("0")).quantize(Decimal("0.01")),
            )
            for label in trend_labels
        ]

        plan_items = [
            RevenuePlanItem(
                plan_name=name,
                amount=amt.quantize(Decimal("0.01")),
            )
            for name, amt in sorted(by_plan.items(), key=lambda x: x[1], reverse=True)
        ]

        return RevenueReport(
            this_month=this_month.quantize(Decimal("0.01")),
            last_month=last_month.quantize(Decimal("0.01")),
            growth_pct=growth_pct,
            by_plan=plan_items,
            monthly_trend=monthly_trend,
        )


# ════════════════════════════════════════════════════════════════
# Private helpers
# ════════════════════════════════════════════════════════════════

def _to_utc(dt: datetime) -> datetime:
    """Ensure datetime is UTC-aware; treat naive datetimes as UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _last_n_month_labels(n: int, ref: datetime) -> list[str]:
    """Return the last n month labels (YYYY-MM) ending at ref's month, oldest first."""
    labels = []
    year, month = ref.year, ref.month
    for _ in range(n):
        labels.append(f"{year}-{month:02d}")
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    labels.reverse()
    return labels


def _monthly_growth(tenants: list[Tenant], months: int = 6) -> list[TenantGrowthPoint]:
    """Build cumulative monthly growth points from a list of Tenant objects."""
    now = datetime.now(timezone.utc)
    labels = _last_n_month_labels(months, now)

    # Count new tenants per month label
    bucket: dict[str, int] = defaultdict(int)
    for t in tenants:
        if t.created_at is None:
            continue
        dt = _to_utc(t.created_at)
        label = f"{dt.year}-{dt.month:02d}"
        if label in labels:
            bucket[label] += 1

    # Compute cumulative count of ALL tenants created up to each month
    # (not just those in the 6-month window)
    points = []
    running_total = 0

    # Count all tenants created before the window
    window_start_year = int(labels[0].split("-")[0])
    window_start_month = int(labels[0].split("-")[1])
    for t in tenants:
        if t.created_at is None:
            continue
        dt = _to_utc(t.created_at)
        if (dt.year, dt.month) < (window_start_year, window_start_month):
            running_total += 1

    for label in labels:
        new = bucket.get(label, 0)
        running_total += new
        points.append(
            TenantGrowthPoint(
                label=label,
                new_tenants=new,
                cumulative=running_total,
            )
        )

    return points
