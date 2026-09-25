from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
import pytest
from sqlalchemy import select
from api.dependencies import CurrentUser
from core.exceptions import ValidationError, ForbiddenError
from services.pos_sale_service import PosSaleService
from tests.test_deployment_regressions import sale, create, call

@pytest.fixture(autouse=True)
def plain_product(H):
    # These tests sell via the zero-option default Variant, so the attached
    # Variant Option Group must not be required (test_required_options_enforced
    # re-enables it explicitly). Real sale_price (9.99) is within the 0.01
    # tolerance of the shared sale() helper's hardcoded unit_price=10.
    H["pvog_a"].is_required=False
    H["user_a"].all_branches=True

@pytest.mark.asyncio
async def test_price_tampering_denied(db,H):
    data=sale(H); data.items[0].unit_price=Decimal(1); data.items[0].total=data.subtotal=data.total=Decimal(1)
    with pytest.raises(ValidationError,match="price changed"): await create(db,H,data)

@pytest.mark.asyncio
async def test_required_options_enforced(db,H):
    H["pvog_a"].is_required=True
    with pytest.raises(ValidationError,match="selections"): await create(db,H,sale(H))

@pytest.mark.asyncio
async def test_foreign_option_denied(db,H):
    from schemas.pos_sale import PosSaleVariantOptionSnapshot
    data=sale(H); data.items[0].options=[PosSaleVariantOptionSnapshot(variant_option_id=H["opt_b"].id,option_name="Foreign")]
    with pytest.raises(ValidationError,match="options"): await create(db,H,data)

@pytest.mark.asyncio
async def test_manual_discount_permission(db,H):
    data=sale(H); data.discount=Decimal(1);data.total=Decimal(9);data.payments[0].amount=Decimal(9)
    with pytest.raises(ValidationError,match="permission"): await create(db,H,data)

@pytest.mark.asyncio
async def test_promotion_redemption_limit(db,H):
    from models.promotion import Promotion
    from services.offer_service import OfferService
    promo=Promotion(id=uuid4(),tenant_id=H["tenant_a"].id,name="Ten percent",type="PERCENTAGE",discount_value=10,max_uses=1,used_count=0,is_active=True,all_branches=True)
    db.add(promo);await db.flush()
    data=sale(H)
    offers=await OfferService(db).calculate(data,H["tenant_a"].id,H["branch_a"].id)
    assert offers[0]["discount"]=="1.00"
    data.promotion_id=promo.id;data.discount=Decimal(1);data.total=Decimal(9);data.payments[0].amount=Decimal(9)
    await create(db,H,data)
    assert promo.used_count==1
    second=data.model_copy(update={"id":uuid4(),"sale_number":"SECOND"})
    with pytest.raises(ValidationError,match="Offer"):await create(db,H,second)

@pytest.mark.asyncio
async def test_free_reward_added_and_checked(db,H):
    from models.promotion import Promotion
    from services.offer_service import OfferService
    promo=Promotion(id=uuid4(),tenant_id=H["tenant_a"].id,name="Buy one get one",type="BXGY",discount_value=0,
        trigger_product_id=H["prod_a"].id,trigger_min_qty=1,reward_product_id=H["prod_a"].id,reward_quantity=1,
        reward_discount_type="FREE",used_count=0,is_active=True,all_branches=True)
    db.add(promo);await db.flush();data=sale(H)
    offers=await OfferService(db).calculate(data,H["tenant_a"].id,H["branch_a"].id)
    assert offers[0]["rewards"][0]["quantity"]=="1"
    data.items[0].quantity=2;data.items[0].total=data.subtotal=Decimal(20)
    data.promotion_id=promo.id;data.discount=Decimal(10)
    receipt=await create(db,H,data)
    assert receipt.total==10 and receipt.items[0].quantity==2

@pytest.mark.asyncio
async def test_platform_suspension_blocks_reset(db,H):
    from models.device import DeviceStatus,SuspendScope
    from services.device_service import DeviceService
    H["device_a"].status=DeviceStatus.SUSPENDED;H["device_a"].suspended_scope=SuspendScope.PLATFORM
    with pytest.raises(ValidationError,match="platform"):await DeviceService(db).reset(H["device_a"].id,H["tenant_a"].id)

@pytest.mark.asyncio
async def test_kitchen_transitions_and_foreign_access(db,H):
    from models.preparation_station import PreparationStation
    from services.kitchen_service import KitchenService
    station=PreparationStation(id=uuid4(),branch_id=H["branch_a"].id,name="Kitchen",is_active=True,display_order=0)
    db.add(station);H["prod_a"].preparation_station_id=station.id;await db.flush()
    await create(db,H,sale(H));svc=KitchenService(db)
    user=CurrentUser(H["user_a"].id,H["tenant_a"].id)
    rows=await svc.queue(H["branch_a"].id,user);assert len(rows)==1
    for status in ("PREPARING","READY","SERVED"):
        result=await svc.advance(H["branch_a"].id,rows[0]["id"],status,user);assert result["status"]==status
    assert await svc.queue(H["branch_a"].id,user)==[]
    from core.exceptions import NotFoundError
    with pytest.raises(NotFoundError):await svc.queue(H["branch_b"].id,user)

@pytest.mark.asyncio
async def test_offline_origin_survives_cashier_change(db,H):
    from core.security import create_offline_proof
    from models.user import User
    from models.sale import Sale
    sender=User(id=uuid4(),tenant_id=H["tenant_a"].id,username="replacement",full_name="Replacement",password_hash="unused",is_active=True,all_branches=True)
    db.add(sender);await db.flush()
    data=sale(H).model_dump(mode="json")
    data["items"][0]["variant_id"]=str(H["default_variant_a"].id)
    data["origin_proof"]=create_offline_proof(H["user_a"].id,H["device_a"].id,H["branch_a"].id,H["tenant_a"].id)
    response=await call(db,{**H,"user_a":sender},"POST","/api/v1/pos/sync/upload",{"sales":[data]},cashier=True)
    assert response.status_code==200,response.text
    body=response.json();assert body["created"]==1,body
    stored=await db.scalar(select(Sale).where(Sale.sale_number==data["sale_number"]))
    assert stored.user_id==H["user_a"].id
    from services.sale_service import SaleService

    dashboard_sales = await SaleService(db).list(
        H["branch_a"].id, H["tenant_a"].id
    )
    dashboard_sale = next(
        row for row in dashboard_sales if row.sale_number == data["sale_number"]
    )
    assert dashboard_sale.cashier_name==H["user_a"].full_name
    assert dashboard_sale.cashier_name!="Replacement"

@pytest.mark.asyncio
async def test_auth_limit_is_enforced(db,H):
    from core.auth_limits import limit_auth
    from fastapi import HTTPException
    from starlette.requests import Request
    from models.platform_setting import PlatformSetting
    existing=await db.get(PlatformSetting,"max_login_attempts")
    if existing: existing.value="3"
    else: db.add(PlatformSetting(key="max_login_attempts",value="3"))
    await db.flush()
    async def receive(): return {"type":"http.request","body":b'{"username":"rate-test"}',"more_body":False}
    for _ in range(3):
        await limit_auth(Request({"type":"http","method":"POST","path":"/api/v1/auth/login","headers":[],"client":("192.0.2.50",123)},receive),db)
    with pytest.raises(HTTPException) as error:
        await limit_auth(Request({"type":"http","method":"POST","path":"/api/v1/auth/login","headers":[],"client":("192.0.2.50",123)},receive),db)
    assert error.value.status_code==429
