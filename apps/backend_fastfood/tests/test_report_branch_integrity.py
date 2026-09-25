from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from api.dependencies import CurrentUser
from api.v1.reports import _report_branch_scope
from core.exceptions import ForbiddenError
from models.branch import Branch
from models.cashier_session import CashierSession
from models.payment import Payment
from models.sale import Sale
from models.user_branch import UserBranch
from models.variant_branch_stock import VariantBranchStock
from services.tenant_report_service import TenantReportService
from services.variant_service import VariantService


@pytest.mark.asyncio
async def test_reports_apply_assigned_branch_scope_and_completed_financials(db, H):
    second = Branch(
        id=uuid4(), business_id=H["biz_a"].id, branch_code="BR_A2",
        name="Alpha Second", is_active=True,
    )
    db.add(second)
    await db.flush()

    completed = Sale(
        id=uuid4(), branch_id=second.id, device_id=H["device_a"].id,
        user_id=H["user_a"].id, sale_number="A2-001",
        sold_at=datetime.now(timezone.utc), subtotal=Decimal("21.00"),
        discount=Decimal("2.00"), tax_amount=Decimal("1.00"),
        total=Decimal("20.00"), status="COMPLETED",
    )
    shift = CashierSession(
        id=uuid4(), device_id=H["device_a"].id, user_id=H["user_a"].id,
        branch_id=second.id, tenant_id=H["tenant_a"].id,
        opened_at=datetime.now(timezone.utc) - timedelta(hours=1),
        status="OPEN", opening_cash=Decimal("0.00"),
    )
    completed.session_id = shift.id
    cancelled = Sale(
        id=uuid4(), branch_id=second.id, device_id=H["device_a"].id,
        user_id=H["user_a"].id, sale_number="A2-CANCELLED",
        sold_at=datetime.now(timezone.utc), subtotal=Decimal("100.00"),
        discount=Decimal("50.00"), tax_amount=Decimal("20.00"),
        total=Decimal("70.00"), status="CANCELLED",
    )
    db.add_all([shift, completed, cancelled])
    await db.flush()
    db.add_all([
        Payment(id=uuid4(), sale_id=completed.id, payment_method="CASH", amount=Decimal("20.00")),
        Payment(
            id=uuid4(), sale_id=completed.id, payment_method="CASH",
            amount=Decimal("999.00"), deleted_at=datetime.now(timezone.utc),
        ),
    ])
    await db.flush()

    svc = TenantReportService(db)
    allowed = {second.id}
    summary = await svc.get_summary(H["tenant_a"].id, None, None, None, allowed)
    assert summary.total_sales == 2
    assert summary.completed_sales == 1
    assert summary.total_revenue == Decimal("20.00")
    assert summary.total_discount == Decimal("2.00")
    assert summary.total_tax == Decimal("1.00")

    branches = await svc.get_by_branch(H["tenant_a"].id, None, None, allowed_branch_ids=allowed)
    assert [(row.branch_id, row.sales_count, row.completed_count, row.revenue) for row in branches] == [
        (second.id, 2, 1, Decimal("20.00")),
    ]

    payments = await svc.get_by_payment_method(
        H["tenant_a"].id, None, None, None, allowed_branch_ids=allowed,
    )
    assert payments[0].total_amount == Decimal("20.00")

    shift_summary = await svc.get_summary(
        H["tenant_a"].id, None, None, None, allowed,
        user_id=H["user_a"].id, session_id=shift.id,
    )
    assert shift_summary.total_sales == 1
    assert shift_summary.total_revenue == Decimal("20.00")
    monthly = await svc.get_monthly(
        H["tenant_a"].id, datetime.now(timezone.utc).year, None, allowed,
        user_id=H["user_a"].id, session_id=shift.id,
    )
    yearly = await svc.get_yearly(
        H["tenant_a"].id, None, allowed,
        user_id=H["user_a"].id, session_id=shift.id,
    )
    assert sum(point.sales_count for point in monthly) == 1
    assert sum(point.sales_count for point in yearly) == 1


@pytest.mark.asyncio
async def test_report_route_scope_rejects_unassigned_branch(db, H):
    db.add(UserBranch(user_id=H["user_a"].id, branch_id=H["branch_a"].id))
    await db.flush()
    current = CurrentUser(user_id=H["user_a"].id, tenant_id=H["tenant_a"].id)
    svc = TenantReportService(db)

    assert await _report_branch_scope(current, svc, None) == {H["branch_a"].id}
    with pytest.raises(ForbiddenError):
        await _report_branch_scope(current, svc, H["branch_b"].id)


@pytest.mark.asyncio
async def test_variant_stock_snapshot_is_limited_to_assigned_branches(db, H):
    second = Branch(
        id=uuid4(), business_id=H["biz_a"].id, branch_code="BR_A3",
        name="Alpha Third", is_active=True,
    )
    H["default_variant_a"].tracks_inventory = True
    db.add(second)
    await db.flush()
    db.add_all([
        VariantBranchStock(
            id=uuid4(), variant_id=H["default_variant_a"].id,
            branch_id=H["branch_a"].id, stock_quantity=4,
        ),
        VariantBranchStock(
            id=uuid4(), variant_id=H["default_variant_a"].id,
            branch_id=second.id, stock_quantity=9,
        ),
    ])
    await db.flush()

    snapshot = await VariantService(db).stock_snapshot(
        H["default_variant_a"], branch_ids={H["branch_a"].id},
    )
    assert snapshot == {str(H["branch_a"].id): 4}
