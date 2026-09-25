# tests/conftest.py
#
# Shared fixtures for all tests.
# Uses real DB sessions with automatic rollback — no test data persists.

from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, ".")

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import hash_password
from db.session import engine
from models.branch import Branch
from models.business import Business
from models.business_template import BusinessTemplate
from models.category import Category
from models.device import Device, DeviceStatus
from models.payment import Payment
from models.product import Product
from models.product_variant_option_group import ProductVariantOptionGroup
from models.refund import Refund
from models.refund_item import RefundItem
from models.sale import Sale
from models.sale_item import SaleItem
from models.tenant import Tenant
from models.user import User
from models.variant import Variant
from models.variant_option import VariantOption
from models.variant_option_group import VariantOptionGroup
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository


# ── Event loop ────────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── DB session (per-test, rolled back) ────────────────────────
#
# Opens a raw connection, starts an outer transaction (never committed),
# and redirects session.commit() → session.flush() so service-layer
# commits write to the connection but never escape to the real DB.
# At teardown the outer transaction is rolled back — nothing persists.

@pytest_asyncio.fixture(scope="function")
async def db() -> AsyncSession:
    conn = await engine.connect()
    await conn.begin()

    session = AsyncSession(bind=conn, expire_on_commit=False)
    session.commit = session.flush  # type: ignore[method-assign]

    yield session

    await session.close()
    await conn.rollback()
    await conn.close()


# ── Shared Business Template (spec requires every Tenant to have one) ──

@pytest_asyncio.fixture(scope="function")
async def business_template(db: AsyncSession) -> BusinessTemplate:
    """A minimal, permissive template — tests exercise policy enforcement
    (tracking_forced_on and legacy pricing flags) via their own dedicated templates."""
    tpl = BusinessTemplate(
        id=uuid4(),
        name=f"Test Template {uuid4().hex[:8]}",
        config={
            "inventory": {"tracking_forced_on": False},
            "pricing": {"require_cost_price": False},
        },
    )
    db.add(tpl)
    await db.flush()
    return tpl


# ── Basic two-tenant fixture (auth tests) ─────────────────────

@pytest_asyncio.fixture(scope="function")
async def two_tenants(db: AsyncSession, business_template: BusinessTemplate):
    """Two tenants each with one user. Used by auth/isolation tests."""
    tenant_repo = TenantRepository(db)
    user_repo   = UserRepository(db)
    password    = "TestPass123!"
    hashed      = hash_password(password)

    tenant_a = await tenant_repo.create(name="Tenant Alpha", tenant_code="ALPHA_TEST", business_template_id=business_template.id)
    user_a   = await user_repo.create(
        tenant_id=tenant_a.id, username="alice", full_name="Alice Alpha",
        password_hash=hashed, email="alice@alpha.test",
    )
    tenant_b = await tenant_repo.create(name="Tenant Beta", tenant_code="BETA_TEST", business_template_id=business_template.id)
    user_b   = await user_repo.create(
        tenant_id=tenant_b.id, username="bob", full_name="Bob Beta",
        password_hash=hashed, email="bob@beta.test",
    )
    await db.flush()

    yield dict(
        tenant_a=tenant_a, tenant_b=tenant_b,
        user_a=user_a,     user_b=user_b,
        password=password,
    )


# ── Full hierarchy fixture (business module tests) ────────────

@pytest_asyncio.fixture(scope="function")
async def H(db: AsyncSession, business_template: BusinessTemplate):
    """
    Builds a complete isolated hierarchy for two tenants.

    Tenant A                          Tenant B
    └─ Business A                     └─ Business B
       ├─ Branch A                       ├─ Branch B
       │  └─ Device A                    │  └─ Device B
       ├─ Category A                     └─ Category B
       │  └─ Product A                      └─ Product B
       │     ├─ default Variant A               └─ default Variant B
       │     └─ VariantOptionGroup A (shared)       └─ VariantOptionGroup B (shared)
       │        └─ VariantOption A                     └─ VariantOption B
       └─ User A                         └─ User B

    All records are rolled back after the test — nothing persists.
    """
    hashed = hash_password("Test1234!")

    # ── Tenants ─────────────────────────────────────────────
    tenant_a = Tenant(id=uuid4(), name="Alpha Corp", tenant_code="ALPHA_BIZ", is_active=True,
                       business_template_id=business_template.id)
    tenant_b = Tenant(id=uuid4(), name="Beta Corp", tenant_code="BETA_BIZ", is_active=True,
                       business_template_id=business_template.id)
    db.add_all([tenant_a, tenant_b])
    await db.flush()

    # ── Users ────────────────────────────────────────────────
    user_a = User(id=uuid4(), tenant_id=tenant_a.id, username="alpha_user",
                  full_name="Alpha User", password_hash=hashed, is_active=True)
    user_b = User(id=uuid4(), tenant_id=tenant_b.id, username="beta_user",
                  full_name="Beta User",  password_hash=hashed, is_active=True)
    db.add_all([user_a, user_b])

    # ── Businesses (replaces Restaurant — one per tenant, spec A2) ──
    biz_a = Business(id=uuid4(), tenant_id=tenant_a.id, name="Business Alpha", is_active=True)
    biz_b = Business(id=uuid4(), tenant_id=tenant_b.id, name="Business Beta", is_active=True)
    db.add_all([biz_a, biz_b])
    await db.flush()

    # ── Branches ─────────────────────────────────────────────
    branch_a = Branch(id=uuid4(), business_id=biz_a.id,
                      branch_code="BR_A", name="Alpha Branch", is_active=True)
    branch_b = Branch(id=uuid4(), business_id=biz_b.id,
                      branch_code="BR_B", name="Beta Branch",  is_active=True)
    db.add_all([branch_a, branch_b])

    # ── Devices ──────────────────────────────────────────────
    _dev_now = datetime.now(timezone.utc)
    device_a = Device(id=uuid4(), branch_id=branch_a.id,
                      device_code="DEV_A", letter="A", name="Alpha POS", device_type="POS",
                      status=DeviceStatus.ACTIVE, activated_at=_dev_now)
    device_b = Device(id=uuid4(), branch_id=branch_b.id,
                      device_code="DEV_B", letter="A", name="Beta POS",  device_type="POS",
                      status=DeviceStatus.ACTIVE, activated_at=_dev_now)
    db.add_all([device_a, device_b])

    # ── Categories ───────────────────────────────────────────
    cat_a = Category(id=uuid4(), business_id=biz_a.id,
                     name="Burgers", display_order=0, is_active=True)
    cat_b = Category(id=uuid4(), business_id=biz_b.id,
                     name="Pizzas",  display_order=0, is_active=True)
    db.add_all([cat_a, cat_b])
    await db.flush()

    # ── Products (no base_price — price lives on the default Variant, spec D1) ──
    prod_a = Product(id=uuid4(), category_id=cat_a.id, product_code="PROD_A",
                     name="Classic Burger", display_order=0, is_active=True)
    prod_b = Product(id=uuid4(), category_id=cat_b.id, product_code="PROD_B",
                     name="Margherita",     display_order=0, is_active=True)
    db.add_all([prod_a, prod_b])
    await db.flush()

    # ── Variant Option Groups (shared at the Business level, spec Part B) ──
    og_a = VariantOptionGroup(id=uuid4(), business_id=biz_a.id, name="Size", is_active=True)
    og_b = VariantOptionGroup(id=uuid4(), business_id=biz_b.id, name="Crust", is_active=True)
    db.add_all([og_a, og_b])
    await db.flush()

    # Attach each group to its product (ProductVariantOptionGroup carries the
    # per-product is_required override — spec Part B).
    # usage_type="specification" here — these tests build real per-product
    # combination Variants (a SKU per Size/Crust choice), which is the
    # legacy behavior kept fully working in the backend even though the
    # dashboard no longer offers it as the default for new attachments.
    pvog_a = ProductVariantOptionGroup(product_id=prod_a.id, option_group_id=og_a.id,
                                        is_required=True, display_order=0, usage_type="specification")
    pvog_b = ProductVariantOptionGroup(product_id=prod_b.id, option_group_id=og_b.id,
                                        is_required=True, display_order=0, usage_type="specification")
    db.add_all([pvog_a, pvog_b])

    # ── Variant Options (no price — pricing lives only on Variant.sale_price) ──
    opt_a = VariantOption(id=uuid4(), option_group_id=og_a.id, name="Large", display_order=0, is_active=True)
    opt_b = VariantOption(id=uuid4(), option_group_id=og_b.id, name="Thin",  display_order=0, is_active=True)
    db.add_all([opt_a, opt_b])

    await db.flush()

    variant_a = Variant(
        id=uuid4(), product_id=prod_a.id, option_value_ids=[str(opt_a.id)],
        combination_key=str(opt_a.id), sale_price=Decimal("11.49"), tracks_inventory=False,
    )
    variant_b = Variant(
        id=uuid4(), product_id=prod_b.id, option_value_ids=[str(opt_b.id)],
        combination_key=str(opt_b.id), sale_price=Decimal("12.99"), tracks_inventory=False,
    )
    default_variant_a = Variant(product_id=prod_a.id, option_value_ids=[], combination_key='',
                                 sale_price=Decimal("9.99"), tracks_inventory=False, is_default=True)
    default_variant_b = Variant(product_id=prod_b.id, option_value_ids=[], combination_key='',
                                 sale_price=Decimal("12.99"), tracks_inventory=False, is_default=True)
    db.add_all([variant_a, variant_b, default_variant_a, default_variant_b])
    await db.flush()

    prod_a.default_variant_id = default_variant_a.id
    prod_b.default_variant_id = default_variant_b.id
    await db.flush()

    # ── Sales (one per tenant) ────────────────────────────────
    sale_a = Sale(
        id=uuid4(), branch_id=branch_a.id, device_id=device_a.id, user_id=user_a.id,
        sale_number="A-001", sold_at=datetime.now(timezone.utc),
        subtotal=Decimal("9.99"), discount=Decimal("0.00"), total=Decimal("9.99"),
        status="COMPLETED",
    )
    sale_b = Sale(
        id=uuid4(), branch_id=branch_b.id, device_id=device_b.id, user_id=user_b.id,
        sale_number="B-001", sold_at=datetime.now(timezone.utc),
        subtotal=Decimal("12.99"), discount=Decimal("0.00"), total=Decimal("12.99"),
        status="COMPLETED",
    )
    db.add_all([sale_a, sale_b])

    # ── Sale Items ───────────────────────────────────────────
    item_a = SaleItem(
        id=uuid4(), sale_id=sale_a.id, product_id=prod_a.id,
        variant_id=default_variant_a.id,
        product_name="Classic Burger", quantity=Decimal("1"),
        unit_price=Decimal("9.99"), discount=Decimal("0.00"), total=Decimal("9.99"),
    )
    item_b = SaleItem(
        id=uuid4(), sale_id=sale_b.id, product_id=prod_b.id,
        variant_id=default_variant_b.id,
        product_name="Margherita", quantity=Decimal("1"),
        unit_price=Decimal("12.99"), discount=Decimal("0.00"), total=Decimal("12.99"),
    )
    db.add_all([item_a, item_b])

    # ── Payments ─────────────────────────────────────────────
    pay_a = Payment(id=uuid4(), sale_id=sale_a.id,
                    payment_method="CASH", amount=Decimal("9.99"))
    pay_b = Payment(id=uuid4(), sale_id=sale_b.id,
                    payment_method="CARD", amount=Decimal("12.99"))
    db.add_all([pay_a, pay_b])

    # ── Refunds ──────────────────────────────────────────────
    refund_a = Refund(
        id=uuid4(), sale_id=sale_a.id, branch_id=branch_a.id, device_id=device_a.id,
        refund_number="REF-A-001", refunded_at=datetime.now(timezone.utc),
        amount=Decimal("9.99"), refund_method="CASH", status="COMPLETED",
    )
    refund_b = Refund(
        id=uuid4(), sale_id=sale_b.id, branch_id=branch_b.id, device_id=device_b.id,
        refund_number="REF-B-001", refunded_at=datetime.now(timezone.utc),
        amount=Decimal("12.99"), refund_method="CARD", status="COMPLETED",
    )
    db.add_all([refund_a, refund_b])

    # ── Refund Items ─────────────────────────────────────────
    ritem_a = RefundItem(
        id=uuid4(), refund_id=refund_a.id, sale_item_id=item_a.id,
        product_name="Classic Burger", quantity=Decimal("1"),
        unit_price=Decimal("9.99"), amount=Decimal("9.99"),
    )
    ritem_b = RefundItem(
        id=uuid4(), refund_id=refund_b.id, sale_item_id=item_b.id,
        product_name="Margherita", quantity=Decimal("1"),
        unit_price=Decimal("12.99"), amount=Decimal("12.99"),
    )
    db.add_all([ritem_a, ritem_b])

    await db.flush()

    yield dict(
        tenant_a=tenant_a,   tenant_b=tenant_b,
        business_template=business_template,
        user_a=user_a,       user_b=user_b,
        biz_a=biz_a,         biz_b=biz_b,
        rest_a=biz_a,        rest_b=biz_b,  # back-compat alias — Business replaces Restaurant (spec A2)
        branch_a=branch_a,   branch_b=branch_b,
        device_a=device_a,   device_b=device_b,
        cat_a=cat_a,         cat_b=cat_b,
        prod_a=prod_a,       prod_b=prod_b,
        default_variant_a=default_variant_a, default_variant_b=default_variant_b,
        variant_a=variant_a, variant_b=variant_b,
        og_a=og_a,           og_b=og_b,
        opt_a=opt_a,         opt_b=opt_b,
        pvog_a=pvog_a,       pvog_b=pvog_b,
        sale_a=sale_a,       sale_b=sale_b,
        item_a=item_a,       item_b=item_b,
        pay_a=pay_a,         pay_b=pay_b,
        refund_a=refund_a,   refund_b=refund_b,
        ritem_a=ritem_a,     ritem_b=ritem_b,
    )
