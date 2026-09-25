"""Deployment regression tests: expected denial and correct settlement.
All records use the existing rollback-isolated fixtures.
"""
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from app.main import app
from db.session import get_db
from core.security import create_access_token, create_cashier_token
from api.dependencies import get_user_permissions
from models.sale_item import SaleItem
from models.device import DeviceStatus
from models.sale import Sale
from schemas.pos_sale import PosSaleCreate, PosSaleItemCreate, PosSalePaymentCreate, PosSaleAddonSelection
from services.pos_sale_service import PosSaleService
from services.user_service import UserService
from services.onboarding_service import OnboardingService
from models.user_branch import UserBranch
from core.exceptions import ValidationError, NotFoundError


def test_every_non_login_api_route_has_a_server_auth_dependency():
    from fastapi.routing import APIRoute

    public = {
        "/api/v1/auth/login", "/api/v1/auth/refresh",
        "/api/v1/auth/forgot-password", "/api/v1/auth/reset-password",
        "/api/v1/pos/auth/activate", "/api/platform/auth/login",
        "/api/platform/auth/refresh", "/api/platform/auth/forgot-password",
        "/api/platform/auth/reset-password",
    }
    guards = {"get_current_user", "get_current_cashier", "get_current_device",
              "get_current_platform_admin", "get_current_platform_user",
              "get_current_pos_user"}

    def dependency_names(dependant):
        names = set()
        for dependency in dependant.dependencies:
            names.add(getattr(dependency.call, "__name__", ""))
            names.update(dependency_names(dependency))
        return names

    unguarded = []
    for route in app.routes:
        if not isinstance(route, APIRoute) or not route.path.startswith("/api/"):
            continue
        if route.path not in public and not (dependency_names(route.dependant) & guards):
            unguarded.append(route.path)
    assert unguarded == []


@pytest.mark.asyncio
async def test_platform_branch_user_count_matches_tenant_access(db, H):
    db.add(UserBranch(user_id=H['user_a'].id, branch_id=H['branch_a'].id))
    await db.flush()
    rows = await OnboardingService(db).list_tenant_branches(H['tenant_a'].id)
    assert len(rows) == 1
    assert rows[0].user_count == 1
    assert rows[0].device_count == 1
    # An all-branches user is counted even without a UserBranch row.
    await db.execute(delete(UserBranch).where(UserBranch.user_id == H['user_a'].id))
    H['user_a'].all_branches = True
    await db.flush()
    rows = await OnboardingService(db).list_tenant_branches(H['tenant_a'].id)
    assert rows[0].user_count == 1


@pytest.mark.asyncio
async def test_dashboard_stats_ignore_orphaned_children_of_deleted_tenant(db, H):
    """Even if a tenant's children are (or become, e.g. from data predating the
    TenantService.delete() cascade below) left "live" while the Tenant row
    itself is soft-deleted, the platform dashboard's aggregate counts must
    not be inflated by that leftover data — every count is joined back to
    a non-deleted Tenant, not just filtered by the child row's own deleted_at."""
    before = await OnboardingService(db).get_dashboard_stats()

    H['tenant_b'].deleted_at = datetime.now(timezone.utc)
    await db.flush()

    after = await OnboardingService(db).get_dashboard_stats()
    assert after.total_tenants == before.total_tenants - 1
    assert after.total_users == before.total_users - 1
    assert after.total_branches == before.total_branches - 1
    assert after.total_devices == before.total_devices - 1


@pytest.mark.asyncio
async def test_tenant_delete_cascades_soft_delete_to_children(db, H):
    """Deleting a tenant must cascade the soft-delete to its Business/Branch/
    Device/Category/Product/User rows, so nothing belonging to a deleted
    tenant can be fetched by a query that filters only that table's own
    deleted_at (the common pattern throughout the codebase)."""
    from models.business import Business
    from models.branch import Branch
    from models.device import Device
    from models.category import Category
    from models.product import Product
    from models.user import User
    from services.tenant_service import TenantService

    ids = {
        'biz_b': H['biz_b'].id, 'branch_b': H['branch_b'].id, 'device_b': H['device_b'].id,
        'cat_b': H['cat_b'].id, 'prod_b': H['prod_b'].id, 'user_b': H['user_b'].id,
        'biz_a': H['biz_a'].id, 'branch_a': H['branch_a'].id, 'user_a': H['user_a'].id,
    }

    async def deleted_at(model, id_):
        row = (await db.execute(select(model).where(model.id == id_))).scalar_one()
        return row.deleted_at

    await TenantService(db).delete(H['tenant_b'].id)
    db.expire_all()  # bulk updates don't sync the identity map — re-fetch from DB

    assert await deleted_at(Business, ids['biz_b']) is not None
    assert await deleted_at(Branch, ids['branch_b']) is not None
    assert await deleted_at(Device, ids['device_b']) is not None
    assert await deleted_at(Category, ids['cat_b']) is not None
    assert await deleted_at(Product, ids['prod_b']) is not None
    assert await deleted_at(User, ids['user_b']) is not None

    # Tenant A's data must be untouched.
    assert await deleted_at(Business, ids['biz_a']) is None
    assert await deleted_at(Branch, ids['branch_a']) is None
    assert await deleted_at(User, ids['user_a']) is None


@pytest.mark.asyncio
async def test_owner_can_hold_a_pos_pin_but_other_protections_still_apply(db, H):
    """The tenant owner/admin must be usable as a POS cashier (able to hold a
    PIN and appear on the staff picker) — unlike deactivate()/update()/
    set_branch_assignment(), set_pin() does not lock the owner out of their
    own tenant, so it must not be blocked by the owner-protection guard."""
    from models.role import Role
    from models.user_role import UserRole
    from core.exceptions import ForbiddenError

    admin_role = Role(id=uuid4(), tenant_id=H["tenant_a"].id, name="Admin", is_active=True)
    db.add(admin_role)
    await db.flush()
    db.add(UserRole(id=uuid4(), user_id=H["user_a"].id, role_id=admin_role.id))
    await db.flush()

    svc = UserService(db)
    updated = await svc.set_pin(H["user_a"].id, H["tenant_a"].id, "1234")
    assert updated.has_pin is True

    # The other owner protections must remain intact — this isn't a blanket
    # removal of _is_protected_owner, only set_pin() was exempted.
    with pytest.raises(ForbiddenError):
        await svc.deactivate(H["user_a"].id, H["tenant_a"].id)


def sale(H, product=None):
    p=product or H["prod_a"]
    return PosSaleCreate(sale_number="AUD-"+uuid4().hex[:10],sold_at=datetime.now(timezone.utc),subtotal=10,total=10,
        items=[PosSaleItemCreate(variant_id=p.default_variant_id,product_id=p.id,product_name=p.name,quantity=1,unit_price=10,total=10)],
        payments=[PosSalePaymentCreate(payment_method="Cash",amount=10)])


async def create(db,H,data):
    return await PosSaleService(db).create(data,H["branch_a"].id,H["device_a"].id,H["user_a"].id,H["tenant_a"].id)


async def call(db,H,method,path,body=None,cashier=False):
    async def override(): yield db
    app.dependency_overrides[get_db]=override
    token=(create_cashier_token(H["user_a"].id,H["device_a"].id,H["branch_a"].id,H["tenant_a"].id)
        if cashier else create_access_token(H["user_a"].id,H["tenant_a"].id))
    try:
        async with AsyncClient(transport=ASGITransport(app=app),base_url="http://audit.local") as client:
            return await client.request(method,path,json=body,headers={"Authorization":"Bearer "+token})
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_prevents_self_escalation_then_unauthorized_profile_edit(db,H):
    assert await get_user_permissions(db,H["user_a"].id,H["tenant_a"].id)==set()
    response=await call(db,H,"PUT",f"/api/v1/users/{H['user_a'].id}/branches",{"all_branches":True,"branch_ids":[]})
    assert response.status_code==403,response.text
    assert await get_user_permissions(db,H["user_a"].id,H["tenant_a"].id)==set()
    response=await call(db,H,"PATCH",f"/api/v1/users/{H['user_a'].id}",{"full_name":"Escalated Name"})
    assert response.status_code==403,response.text



@pytest.mark.asyncio
async def test_prevents_cross_tenant_branch_assignment(db,H):
    with pytest.raises(NotFoundError):
        await UserService(db).set_branch_assignment(H["user_a"].id,H["tenant_a"].id,False,[H["branch_b"].id])



@pytest.mark.asyncio
async def test_prevents_cross_tenant_product_in_sale(db,H):
    with pytest.raises(ValidationError):
        await create(db,H,sale(H,H["prod_b"]))



@pytest.mark.asyncio
async def test_prevents_completed_unpaid_sale(db,H):
    data=sale(H)
    data.payments=[]
    with pytest.raises(ValidationError):
        await create(db,H,data)


@pytest.mark.asyncio
async def test_prevents_paid_customization_rejected(db,H):
    """A legitimately priced Add-on selection is accepted, and the server
    re-verifies the price against AddonItem.price_delta rather than trusting
    the client-submitted value (spec D7)."""
    from services.addon_group_service import AddonGroupService
    from services.addon_item_service import AddonItemService
    from schemas.addon_group import AddonGroupCreate
    from schemas.addon_item import AddonItemCreate

    group = await AddonGroupService(db).create(H["biz_a"].id, H["tenant_a"].id, AddonGroupCreate(name="Extras"))
    addon = await AddonItemService(db).create(
        group.id, H["tenant_a"].id, AddonItemCreate(name="Extra Cheese", price_delta=Decimal("2.00")),
    )

    data=sale(H)
    data.items[0].addons=[PosSaleAddonSelection(addon_item_id=addon.id,addon_name="Extra Cheese",price_delta=Decimal("2.00"))]
    data.items[0].total=Decimal(12)
    data.subtotal=data.total=Decimal(12)
    data.payments[0].amount=Decimal(12)
    receipt=await create(db,H,data)
    assert receipt.total == Decimal(12)


@pytest.mark.asyncio
async def test_prevents_suspended_device_and_inactive_cashier_sale(db,H):
    H["device_a"].status=DeviceStatus.SUSPENDED
    H["user_a"].is_active=False
    await db.flush()
    response=await call(db,H,"POST","/api/v1/pos/sales/",sale(H).model_dump(mode="json"),cashier=True)
    assert response.status_code in (401,403),response.text


@pytest.mark.asyncio
async def test_prevents_deactivated_tenant_dashboard_access(db,H):
    H["tenant_a"].is_active=False
    H["user_a"].is_active=False
    await db.flush()
    response=await call(db,H,"GET","/api/v1/users/")
    assert response.status_code==401,response.text


@pytest.mark.asyncio
async def test_prevents_disabled_sales_module_pos_bypass(db,H,business_template):
    # Module visibility is now Business-Template-driven (config.modules.hidden)
    # rather than a per-tenant override — hiding "sales" on tenant_a's
    # template is what used to be H["tenant_a"].enabled_modules=[...].
    business_template.config = {**business_template.config, "modules": {"hidden": ["sales"]}}
    await db.flush()
    denied=await call(db,H,"GET",f"/api/v1/sales/?branch_id={H['branch_a'].id}")
    assert denied.status_code==403,denied.text
    response=await call(db,H,"POST","/api/v1/pos/sales/",sale(H).model_dump(mode="json"),cashier=True)
    assert response.status_code in (401,403),response.text


@pytest.mark.asyncio
async def test_prevents_missing_shift_attribution(db,H):
    receipt=await create(db,H,sale(H))
    stored=await db.get(Sale,receipt.sale_id)
    assert stored.session_id is None


@pytest.mark.asyncio
async def test_prevents_cross_tenant_role_assignment(db,H):
    from schemas.role import RoleCreate
    from services.role_service import RoleService
    svc=RoleService(db)
    role=await svc.create(H["tenant_a"].id,RoleCreate(name="Admin"))
    with pytest.raises(NotFoundError):
        await svc.assign_user_role(H["user_b"].id,role.id,H["tenant_a"].id)
    assert await get_user_permissions(db,H["user_b"].id,H["tenant_b"].id)==set()


@pytest.mark.asyncio
async def test_role_and_permission_can_be_restored_after_revocation(db, H):
    from models.permission import Permission
    from schemas.role import RoleCreate
    from services.role_service import RoleService

    svc = RoleService(db)
    role = await svc.create(H["tenant_a"].id, RoleCreate(name="Limited Reader"))
    permission = await db.scalar(select(Permission).where(Permission.code == "sales.view"))
    if permission is None:
        permission = Permission(id=uuid4(), code="sales.view", name="View Sales",
                                module="sales", is_active=True)
        db.add(permission)
        await db.flush()

    await svc.assign_permission(role.id, permission.id, H["tenant_a"].id)
    await svc.assign_user_role(H["user_a"].id, role.id, H["tenant_a"].id)
    assert "sales.view" in await get_user_permissions(db, H["user_a"].id, H["tenant_a"].id)

    await svc.remove_permission(role.id, permission.id, H["tenant_a"].id)
    assert "sales.view" not in await get_user_permissions(db, H["user_a"].id, H["tenant_a"].id)
    await svc.assign_permission(role.id, permission.id, H["tenant_a"].id)
    assert "sales.view" in await get_user_permissions(db, H["user_a"].id, H["tenant_a"].id)

    await svc.remove_user_role(H["user_a"].id, role.id, H["tenant_a"].id)
    assert "sales.view" not in await get_user_permissions(db, H["user_a"].id, H["tenant_a"].id)
    await svc.assign_user_role(H["user_a"].id, role.id, H["tenant_a"].id)
    assert "sales.view" in await get_user_permissions(db, H["user_a"].id, H["tenant_a"].id)



@pytest.mark.asyncio
async def test_prevents_repeated_refund_over_original_value(db,H):
    from schemas.refund import RefundCreate,RefundItemCreate
    from services.refund_service import RefundService
    receipt=await create(db,H,sale(H))
    item=await db.scalar(select(SaleItem).where(SaleItem.sale_id==receipt.sale_id))
    for attempt in range(2):
        data=RefundCreate(sale_id=receipt.sale_id,branch_id=H["branch_a"].id,device_id=H["device_a"].id,
            refund_number="AUD-R-"+uuid4().hex[:10],refunded_at=datetime.now(timezone.utc),amount=10,refund_method="Cash",
            items=[RefundItemCreate(sale_item_id=item.id,product_name=item.product_name,quantity=1,unit_price=10,amount=10)])
        if attempt == 0:
            result=await RefundService(db).create(data,H["tenant_a"].id)
            assert result.amount==10
        else:
            with pytest.raises(ValidationError):
                await RefundService(db).create(data,H["tenant_a"].id)


@pytest.mark.asyncio
async def test_prevents_change_counted_as_revenue(db,H):
    from services.tenant_report_service import TenantReportService
    data=sale(H)
    data.payments[0].amount=Decimal(20)
    receipt=await create(db,H,data)
    assert receipt.total==10 and receipt.change==10
    # Payment reporting sums tendered money, including the returned change.
    report=await TenantReportService(db).get_by_payment_method(H["tenant_a"].id,None,None,None)
    cash=next(x for x in report[0].breakdown if x.payment_method=="Cash")
    assert cash.amount==Decimal("19.99")  # fixture 9.99 + tendered 20, actual collection 19.99


@pytest.mark.asyncio
async def test_prevents_tenant_token_read_and_modify_another_tenant(db,H):
    response=await call(db,H,"GET",f"/api/v1/tenants/{H['tenant_b'].id}")
    assert response.status_code in (404,405),response.text
    response=await call(db,H,"PATCH",f"/api/v1/tenants/{H['tenant_b'].id}",{"name":"AUDIT cross-tenant change"})
    assert response.status_code in (404,405),response.text



@pytest.mark.asyncio
async def test_prevents_tenant_bypass_platform_device_suspension(db,H):
    from services.device_service import DeviceService
    from models.device import SuspendScope
    H["device_a"].status=DeviceStatus.SUSPENDED
    H["device_a"].suspended_scope=SuspendScope.PLATFORM
    await db.flush()
    svc=DeviceService(db)
    await svc.suspend(H["device_a"].id,H["tenant_a"].id)
    assert H["device_a"].suspended_scope == SuspendScope.PLATFORM
    with pytest.raises(ValidationError):
        await svc.reactivate(H["device_a"].id,H["tenant_a"].id)


@pytest.fixture(autouse=True)
def plain_product_fixture(H):
    # These settlement/inventory tests sell via the zero-option default
    # Variant, so the attached Variant Option Group must not be required.
    H["pvog_a"].is_required = False


@pytest.mark.asyncio
async def test_tracked_sale_and_refund_with_autoflush_disabled(db, H):
    from services.variant_service import VariantService
    from services.refund_service import RefundService
    from schemas.refund import RefundCreate, RefundItemCreate
    H['prod_a'].allow_inventory_tracking = True
    await db.flush()
    service = VariantService(db, created_by=H['user_a'].id)
    variant = H['default_variant_a']
    await service.set_tracking(H['tenant_a'].id, variant.id, True, {str(H['branch_a'].id): 8})
    db.autoflush = False
    receipt = await create(db, H, sale(H))
    line = await db.scalar(select(SaleItem).where(SaleItem.sale_id == receipt.sale_id))
    assert line.tracked_at_sale is True
    row = await service.get_branch_stock_row(variant.id, H['branch_a'].id)
    assert row.stock_quantity == 7
    refund = RefundCreate(sale_id=receipt.sale_id, branch_id=H['branch_a'].id, device_id=H['device_a'].id,
        refund_number='R-' + uuid4().hex[:10], refunded_at=datetime.now(timezone.utc), amount=10, refund_method='Cash',
        items=[RefundItemCreate(sale_item_id=line.id, product_name=line.product_name, quantity=1, unit_price=10, amount=10)])
    await RefundService(db).create(refund, H['tenant_a'].id, created_by=H['user_a'].id)
    row = await service.get_branch_stock_row(variant.id, H['branch_a'].id)
    assert row.stock_quantity == 8
    rows = await service.history(H['tenant_a'].id, variant.id)
    assert [r.change_type for r in rows] == ['refund', 'sale', 'opening']
    assert all(r.created_by == H['user_a'].id for r in rows)
