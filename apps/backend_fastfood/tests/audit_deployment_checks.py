"""Audit probes: PASS means the documented defect was reproduced, not fixed.

Refreshed after the Business/Variant/Add-on refactor (spec Part A-J) — model
references updated (Restaurant -> Business, options -> variant options/add-ons,
variant_id now required on every sale item). Where the refactor structurally
closed a finding, the probe was rewritten to assert the FIXED behavior instead
and is named accordingly; the DEPLOYMENT_AUDIT.md doc explains which is which.

All records use the existing rollback-isolated fixtures.
"""
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from app.main import app
from db.session import get_db
from core.security import create_access_token, create_cashier_token
from api.dependencies import get_user_permissions
from models.sale_item import SaleItem
from models.device import DeviceStatus
from models.sale import Sale
from models.addon_group import AddonGroup
from models.addon_item import AddonItem
from schemas.pos_sale import (
    PosSaleCreate,
    PosSaleItemCreate,
    PosSalePaymentCreate,
    PosSaleAddonSelection,
    PosSaleVariantOptionSnapshot,
)
from services.pos_sale_service import PosSaleService
from services.user_service import UserService
from core.exceptions import ValidationError


def sale(H, product=None, variant=None):
    p = product or H["prod_a"]
    is_a = p is H["prod_a"]
    v = variant or (H["variant_a"] if is_a else H["variant_b"])
    opt = H["opt_a"] if is_a else H["opt_b"]
    # Non-default variants carry one option per attached group — the server
    # cross-checks this snapshot against the variant's combination_key.
    options = [PosSaleVariantOptionSnapshot(variant_option_id=opt.id, option_name=opt.name)] \
        if v.option_value_ids else []
    price = v.sale_price  # server re-verifies unit_price against Variant.sale_price
    return PosSaleCreate(sale_number="AUD-" + uuid4().hex[:10], sold_at=datetime.now(timezone.utc), subtotal=price, total=price,
        items=[PosSaleItemCreate(variant_id=v.id, product_id=p.id, product_name=p.name, quantity=1, unit_price=price, total=price,
                                  options=options)],
        payments=[PosSalePaymentCreate(payment_method="Cash", amount=price)])


async def create(db, H, data):
    return await PosSaleService(db).create(data, H["branch_a"].id, H["device_a"].id, H["user_a"].id, H["tenant_a"].id)


async def call(db, H, method, path, body=None, cashier=False):
    async def override(): yield db
    app.dependency_overrides[get_db] = override
    token = (create_cashier_token(H["user_a"].id, H["device_a"].id, H["branch_a"].id, H["tenant_a"].id)
        if cashier else create_access_token(H["user_a"].id, H["tenant_a"].id))
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://audit.local") as client:
            return await client.request(method, path, json=body, headers={"Authorization": "Bearer " + token})
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_prevents_self_escalation_then_unauthorized_profile_edit(db, H):
    # Structurally closed since this probe was last written: "Free Guest" (and
    # its per-field can_free_guest escalation vector) is retired — replaced by
    # the sales.discount permission, granted only through Roles (never a
    # single PATCH field) — rewritten to assert the FIXED behavior per this
    # file's own convention for closed findings.
    assert await get_user_permissions(db, H["user_a"].id, H["tenant_a"].id) == set()
    response = await call(db, H, "PUT", f"/api/v1/users/{H['user_a'].id}/branches", {"all_branches": True, "branch_ids": []})
    assert response.status_code == 403, response.text
    assert await get_user_permissions(db, H["user_a"].id, H["tenant_a"].id) == set()
    response = await call(db, H, "PATCH", f"/api/v1/users/{H['user_a'].id}", {"full_name": "Escalated Name"})
    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_reproduces_cross_tenant_branch_assignment(db, H):
    result = await UserService(db).set_branch_assignment(H["user_a"].id, H["tenant_a"].id, False, [H["branch_b"].id])
    assert result.branches[0].id == H["branch_b"].id
    assert result.branches[0].name == H["branch_b"].name


@pytest.mark.asyncio
async def test_reproduces_cross_tenant_product_in_sale(db, H):
    receipt = await create(db, H, sale(H, H["prod_b"], H["variant_b"]))
    item = await db.scalar(select(SaleItem).where(SaleItem.sale_id == receipt.sale_id))
    assert item.product_id == H["prod_b"].id


@pytest.mark.asyncio
async def test_reproduces_completed_unpaid_sale(db, H):
    data = sale(H)
    data.payments = []
    receipt = await create(db, H, data)
    stored = await db.get(Sale, receipt.sale_id)
    assert stored.status == "COMPLETED" and receipt.total == 10 and receipt.payments == []


@pytest.mark.asyncio
async def test_fixed_addon_priced_customization_now_accepted(db, H):
    """Was A13 'valid paid customizations fail checkout'. Options no longer carry
    a price (spec A1/D4) — the equivalent paid-customization path is an Add-on,
    server-priced end to end (D7). A correctly computed total must now succeed."""
    group = AddonGroup(id=uuid4(), business_id=H["biz_a"].id, name="Extras", selection_type="multiple",
                        min_select=0, max_select=None)
    db.add(group)
    await db.flush()
    item = AddonItem(id=uuid4(), addon_group_id=group.id, name="Extra Cheese", price_delta=Decimal("2.00"),
                      default_selected=False, display_order=0, is_active=True)
    db.add(item)
    await db.flush()

    data = sale(H)
    priced_total = H["variant_a"].sale_price + Decimal("2.00")
    data.items[0].addons = [PosSaleAddonSelection(addon_item_id=item.id, addon_name="Extra Cheese", price_delta=Decimal("2.00"))]
    data.items[0].total = priced_total
    data.subtotal = data.total = priced_total
    data.payments[0].amount = priced_total
    receipt = await create(db, H, data)
    assert receipt.total == priced_total
    assert receipt.items[0].addons[0].price_delta == Decimal("2.00")


@pytest.mark.asyncio
async def test_fixed_tampered_addon_price_still_rejected(db, H):
    """D7: a client that lies about an add-on's price_delta cannot get it for
    free — the server always recomputes from AddonItem, so a total computed
    from the tampered (zero) price still mismatches and is rejected."""
    group = AddonGroup(id=uuid4(), business_id=H["biz_a"].id, name="Extras", selection_type="multiple",
                        min_select=0, max_select=None)
    db.add(group)
    await db.flush()
    item = AddonItem(id=uuid4(), addon_group_id=group.id, name="Extra Cheese", price_delta=Decimal("2.00"),
                      default_selected=False, display_order=0, is_active=True)
    db.add(item)
    await db.flush()

    data = sale(H)
    # Client claims the add-on is free and submits a total that assumes that.
    data.items[0].addons = [PosSaleAddonSelection(addon_item_id=item.id, addon_name="Extra Cheese", price_delta=Decimal("0.00"))]
    with pytest.raises(ValidationError, match="total mismatch"):
        await create(db, H, data)


@pytest.mark.asyncio
async def test_reproduces_suspended_device_and_inactive_cashier_sale(db, H):
    H["device_a"].status = DeviceStatus.SUSPENDED
    H["user_a"].is_active = False
    await db.flush()
    response = await call(db, H, "POST", "/api/v1/pos/sales/", sale(H).model_dump(mode="json"), cashier=True)
    assert response.status_code == 201, response.text


@pytest.mark.asyncio
async def test_reproduces_deactivated_tenant_dashboard_access(db, H):
    H["tenant_a"].is_active = False
    H["user_a"].is_active = False
    await db.flush()
    response = await call(db, H, "GET", "/api/v1/users/")
    assert response.status_code == 200, response.text


@pytest.mark.asyncio
async def test_prevents_disabled_sales_module_pos_bypass(db, H, business_template):
    # Structurally closed since this probe was last written: module
    # visibility moved from a per-tenant enabled_modules override to
    # Business-Template config.modules.hidden (see api/dependencies.py's
    # tenant_enabled_modules), and api/v1/pos/_guards.py's
    # operational_cashier() already blocks a POS sale when "sales" is
    # hidden — rewritten to assert the FIXED behavior per this file's own
    # convention for closed findings.
    from models.user_branch import UserBranch
    db.add(UserBranch(user_id=H["user_a"].id, branch_id=H["branch_a"].id))
    business_template.config = {**business_template.config, "modules": {"hidden": ["sales"]}}
    await db.flush()
    denied = await call(db, H, "GET", f"/api/v1/sales/?branch_id={H['branch_a'].id}")
    assert denied.status_code == 403, denied.text
    response = await call(db, H, "POST", "/api/v1/pos/sales/", sale(H).model_dump(mode="json"), cashier=True)
    assert response.status_code in (401, 403), response.text


@pytest.mark.asyncio
async def test_reproduces_missing_shift_attribution(db, H):
    receipt = await create(db, H, sale(H))
    stored = await db.get(Sale, receipt.sale_id)
    assert stored.session_id is None


@pytest.mark.asyncio
async def test_reproduces_cross_tenant_role_assignment(db, H):
    from schemas.role import RoleCreate
    from services.role_service import RoleService
    svc = RoleService(db)
    role = await svc.create(H["tenant_a"].id, RoleCreate(name="Admin"))
    await svc.assign_user_role(H["user_b"].id, role.id, H["tenant_a"].id)
    assert await get_user_permissions(db, H["user_b"].id, H["tenant_b"].id) == {"*"}


@pytest.mark.asyncio
async def test_reproduces_repeated_refund_over_original_value(db, H):
    from schemas.refund import RefundCreate, RefundItemCreate
    from services.refund_service import RefundService
    receipt = await create(db, H, sale(H))
    item = await db.scalar(select(SaleItem).where(SaleItem.sale_id == receipt.sale_id))
    for _ in range(2):
        data = RefundCreate(sale_id=receipt.sale_id, branch_id=H["branch_a"].id, device_id=H["device_a"].id,
            refund_number="AUD-R-" + uuid4().hex[:10], refunded_at=datetime.now(timezone.utc), amount=item.total, refund_method="Cash",
            items=[RefundItemCreate(sale_item_id=item.id, product_name=item.product_name, quantity=1, unit_price=item.unit_price, amount=item.total)])
        result = await RefundService(db).create(data, H["tenant_a"].id)
        assert result.amount == item.total


@pytest.mark.asyncio
async def test_fixed_change_not_counted_as_revenue(db, H):
    """Was A11 'cash change is counted as collected revenue'. Payment now
    stores tendered_amount (raw) separately from amount (net of returned
    change, see pos_sale_service.py:251-263) — reporting sums the net."""
    from services.tenant_report_service import TenantReportService
    data = sale(H)
    tendered = Decimal(20)
    price = H["variant_a"].sale_price
    data.payments[0].amount = tendered
    receipt = await create(db, H, data)
    assert receipt.total == price and receipt.change == tendered - price
    report = await TenantReportService(db).get_by_payment_method(H["tenant_a"].id, None, None, None)
    cash = next(x for x in report[0].breakdown if x.payment_method == "Cash")
    assert cash.amount == Decimal("9.99") + price  # fixture 9.99 + this sale's NET collected cash


@pytest.mark.asyncio
async def test_fixed_legacy_tenants_router_not_mounted(db, H):
    """Was A01 'critical: tenant credentials can access other tenants' via the
    unmounted-but-importable legacy /api/v1/tenants router. That router is now
    verified NOT mounted in app/main.py (api/v1/tenants.py carries an explicit
    NOTE to that effect) — the request must 404, not reach TenantService."""
    response = await call(db, H, "GET", f"/api/v1/tenants/{H['tenant_b'].id}")
    assert response.status_code == 404, response.text


@pytest.mark.asyncio
async def test_reproduces_tenant_bypass_platform_device_suspension(db, H):
    from services.device_service import DeviceService
    from models.device import SuspendScope
    H["device_a"].status = DeviceStatus.SUSPENDED
    H["device_a"].suspended_scope = SuspendScope.PLATFORM
    await db.flush()
    svc = DeviceService(db)
    await svc.suspend(H["device_a"].id, H["tenant_a"].id)
    result = await svc.reactivate(H["device_a"].id, H["tenant_a"].id)
    assert result.status == DeviceStatus.ACTIVE
