# tests/test_variant_display_names.py
#
# Every stock-mutation endpoint (increase/decrease/set/transfer) must return
# a populated product_name/variant_name, not just the list endpoint —
# api/v1/variants.py::_to_response() used to leave these null outside
# list_variants(), and the tenant dashboard's optimistic row merge
# (`{...cachedRow, ...serverResponse}`) then overwrote the previously
# correct cached name with null, showing "SKU <id-prefix>" after any stock
# action (e.g. Increase) instead of the real product/variant name.

from __future__ import annotations
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from core.security import create_access_token
from db.session import get_db
from models.branch import Branch
from models.role import Role
from models.user_role import UserRole


async def _grant_admin(db, user, tenant_id):
    role = Role(id=uuid4(), tenant_id=tenant_id, name="Admin", is_active=True)
    db.add(role)
    await db.flush()
    db.add(UserRole(id=uuid4(), user_id=user.id, role_id=role.id))
    # branch_access.py's enforce_branch_request otherwise 403s any branch
    # unless the user is explicitly assigned or all_branches — irrelevant to
    # what this test file checks (name population), so bypass it plainly.
    user.all_branches = True
    await db.flush()


async def _call(db, tenant_id, user_id, method, path, body=None):
    async def override():
        yield db
    app.dependency_overrides[get_db] = override
    try:
        token = create_access_token(user_id, tenant_id)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test.local") as client:
            return await client.request(method, path, json=body, headers={"Authorization": "Bearer " + token})
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_increase_stock_response_includes_product_and_variant_name(db, H):
    await _grant_admin(db, H["user_a"], H["tenant_a"].id)
    variant = H["variant_a"]
    variant.tracks_inventory = True
    H["prod_a"].allow_inventory_tracking = True
    await db.flush()

    resp = await _call(
        db, H["tenant_a"].id, H["user_a"].id, "POST",
        f"/api/v1/variants/{variant.id}/stock/increase?branch_id={H['branch_a'].id}",
        {"quantity": 3},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["product_name"] == "Classic Burger"
    assert body["variant_name"] == "Size: Large"


@pytest.mark.asyncio
async def test_set_stock_response_includes_product_and_variant_name(db, H):
    await _grant_admin(db, H["user_a"], H["tenant_a"].id)
    variant = H["variant_a"]
    variant.tracks_inventory = True
    H["prod_a"].allow_inventory_tracking = True
    await db.flush()

    resp = await _call(
        db, H["tenant_a"].id, H["user_a"].id, "POST",
        f"/api/v1/variants/{variant.id}/stock?branch_id={H['branch_a'].id}",
        {"stock_quantity": 10},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["product_name"] == "Classic Burger"
    assert body["variant_name"] == "Size: Large"


@pytest.mark.asyncio
async def test_transfer_stock_response_includes_product_and_variant_name(db, H):
    await _grant_admin(db, H["user_a"], H["tenant_a"].id)
    variant = H["variant_a"]
    variant.tracks_inventory = True
    H["prod_a"].allow_inventory_tracking = True
    other_branch = Branch(id=uuid4(), business_id=H["biz_a"].id, branch_code="BR_A2",
                           name="Alpha Branch 2", is_active=True)
    db.add(other_branch)
    await db.flush()

    # Seed source-branch stock via increase first (also exercises that path).
    seed = await _call(
        db, H["tenant_a"].id, H["user_a"].id, "POST",
        f"/api/v1/variants/{variant.id}/stock?branch_id={H['branch_a'].id}",
        {"stock_quantity": 5},
    )
    assert seed.status_code == 200, seed.text

    resp = await _call(
        db, H["tenant_a"].id, H["user_a"].id, "POST",
        f"/api/v1/variants/{variant.id}/transfer",
        {"from_branch_id": str(H["branch_a"].id), "to_branch_id": str(other_branch.id), "quantity": 2},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["product_name"] == "Classic Burger"
    assert body["variant_name"] == "Size: Large"
