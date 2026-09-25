# tests/test_api_categories.py
#
# HTTP-level tests for POST/GET/PATCH/DELETE /api/v1/categories
# Uses httpx.AsyncClient against the real FastAPI app.
# The get_db dependency is overridden to inject the test session so all
# writes stay within the per-test transaction that is rolled back at teardown.

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from core.security import create_access_token
from db.session import get_db

BASE = "/api/v1/categories"


# ── fixtures ────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client(db: AsyncSession, H):
    """
    AsyncClient wired to the FastAPI app with get_db overridden.
    H fixture data is pre-loaded into the same test session so the API
    can see both tenants, businesses, categories, etc.
    """
    from models.role import Role
    from models.user_role import UserRole
    from uuid import uuid4
    for suffix in ("a", "b"):
        role = Role(id=uuid4(), tenant_id=H["tenant_" + suffix].id, name="Admin", is_active=True)
        db.add(role)
        db.add(UserRole(id=uuid4(), user_id=H["user_" + suffix].id, role_id=role.id))
    await db.flush()
    async def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as c:
            yield c
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def token_a(H) -> str:
    return create_access_token(H["user_a"].id, H["tenant_a"].id)


@pytest.fixture
def token_b(H) -> str:
    return create_access_token(H["user_b"].id, H["tenant_b"].id)


@pytest.fixture
def auth_a(token_a) -> dict:
    return {"Authorization": f"Bearer {token_a}"}


@pytest.fixture
def auth_b(token_b) -> dict:
    return {"Authorization": f"Bearer {token_b}"}


# ── POST /categories/ ────────────────────────────────────────────────────────

class TestCreateCategory:

    @pytest.mark.asyncio
    async def test_create_returns_201(self, client, H, auth_a):
        resp = await client.post(
            BASE + "/",
            json={"name": "Desserts", "display_order": 2},
            headers=auth_a,
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "Desserts"
        assert body["display_order"] == 2
        assert body["is_active"] is True
        assert body["business_id"] == str(H["biz_a"].id)
        assert "id" in body

    @pytest.mark.asyncio
    async def test_create_with_description(self, client, H, auth_a):
        resp = await client.post(
            BASE + "/",
            json={"name": "Sides", "description": "Fries and more", "display_order": 3},
            headers=auth_a,
        )
        assert resp.status_code == 201
        assert resp.json()["description"] == "Fries and more"

    @pytest.mark.asyncio
    async def test_create_without_token_returns_401(self, client, H):
        resp = await client.post(
            BASE + "/",
            json={"name": "No Auth"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_create_missing_name_returns_422(self, client, H, auth_a):
        resp = await client.post(
            BASE + "/",
            json={"display_order": 0},
            headers=auth_a,
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_create_needs_no_business_id_param(
        self, client, H, auth_a
    ):
        """business_id is resolved server-side from the caller's tenant
        (a tenant has exactly one Business, spec A2) — no query param needed."""
        resp = await client.post(
            BASE + "/",
            json={"name": "No Business Param"},
            headers=auth_a,
        )
        assert resp.status_code == 201


# ── GET /categories/ ────────────────────────────────────────────────────────

class TestListCategories:

    @pytest.mark.asyncio
    async def test_list_returns_200(self, client, H, auth_a):
        resp = await client.get(
            BASE + "/",
            headers=auth_a,
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.asyncio
    async def test_list_contains_own_category(self, client, H, auth_a):
        resp = await client.get(
            BASE + "/",
            headers=auth_a,
        )
        ids = [c["id"] for c in resp.json()]
        assert str(H["cat_a"].id) in ids

    @pytest.mark.asyncio
    async def test_list_does_not_leak_other_tenant_category(
        self, client, H, auth_a
    ):
        resp = await client.get(
            BASE + "/",
            headers=auth_a,
        )
        ids = [c["id"] for c in resp.json()]
        assert str(H["cat_b"].id) not in ids

    @pytest.mark.asyncio
    async def test_list_without_token_returns_401(self, client, H):
        resp = await client.get(
            BASE + "/",
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_list_inactive_hidden_by_default(self, client, H, auth_a):
        # Deactivate cat_a via the API
        await client.post(
            f"{BASE}/{H['cat_a'].id}/deactivate", headers=auth_a
        )
        resp = await client.get(
            BASE + "/",
            headers=auth_a,
        )
        ids = [c["id"] for c in resp.json()]
        assert str(H["cat_a"].id) not in ids

    @pytest.mark.asyncio
    async def test_list_include_inactive_flag(self, client, H, auth_a):
        await client.post(
            f"{BASE}/{H['cat_a'].id}/deactivate", headers=auth_a
        )
        resp = await client.get(
            BASE + "/",
            params={"include_inactive": True},
            headers=auth_a,
        )
        ids = [c["id"] for c in resp.json()]
        assert str(H["cat_a"].id) in ids


# ── GET /categories/{id} ────────────────────────────────────────────────────

class TestGetCategory:

    @pytest.mark.asyncio
    async def test_get_own_returns_200(self, client, H, auth_a):
        resp = await client.get(f"{BASE}/{H['cat_a'].id}", headers=auth_a)
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == str(H["cat_a"].id)
        assert body["name"] == H["cat_a"].name

    @pytest.mark.asyncio
    async def test_get_other_tenant_returns_404(self, client, H, auth_a):
        resp = await client.get(f"{BASE}/{H['cat_b'].id}", headers=auth_a)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_404(self, client, H, auth_a):
        from uuid import uuid4
        resp = await client.get(f"{BASE}/{uuid4()}", headers=auth_a)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_without_token_returns_401(self, client, H):
        resp = await client.get(f"{BASE}/{H['cat_a'].id}")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_get_with_tenant_b_token_sees_own_category(
        self, client, H, auth_b
    ):
        resp = await client.get(f"{BASE}/{H['cat_b'].id}", headers=auth_b)
        assert resp.status_code == 200
        assert resp.json()["id"] == str(H["cat_b"].id)

    @pytest.mark.asyncio
    async def test_response_schema_has_required_fields(self, client, H, auth_a):
        resp = await client.get(f"{BASE}/{H['cat_a'].id}", headers=auth_a)
        body = resp.json()
        for field in ("id", "business_id", "name", "display_order", "is_active",
                      "created_at", "updated_at"):
            assert field in body, f"Missing field: {field}"


# ── PATCH /categories/{id} ──────────────────────────────────────────────────

class TestUpdateCategory:

    @pytest.mark.asyncio
    async def test_patch_name_returns_200(self, client, H, auth_a):
        resp = await client.patch(
            f"{BASE}/{H['cat_a'].id}",
            json={"name": "Updated Burgers"},
            headers=auth_a,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Burgers"

    @pytest.mark.asyncio
    async def test_patch_display_order(self, client, H, auth_a):
        resp = await client.patch(
            f"{BASE}/{H['cat_a'].id}",
            json={"display_order": 99},
            headers=auth_a,
        )
        assert resp.status_code == 200
        assert resp.json()["display_order"] == 99

    @pytest.mark.asyncio
    async def test_patch_partial_only_changes_given_fields(self, client, H, auth_a):
        original_order = H["cat_a"].display_order
        resp = await client.patch(
            f"{BASE}/{H['cat_a'].id}",
            json={"name": "New Name"},
            headers=auth_a,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "New Name"
        assert body["display_order"] == original_order

    @pytest.mark.asyncio
    async def test_patch_other_tenant_returns_404(self, client, H, auth_a):
        resp = await client.patch(
            f"{BASE}/{H['cat_b'].id}",
            json={"name": "Stolen"},
            headers=auth_a,
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_patch_nonexistent_returns_404(self, client, H, auth_a):
        from uuid import uuid4
        resp = await client.patch(
            f"{BASE}/{uuid4()}",
            json={"name": "Ghost"},
            headers=auth_a,
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_patch_without_token_returns_401(self, client, H):
        resp = await client.patch(
            f"{BASE}/{H['cat_a'].id}", json={"name": "X"}
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_patch_empty_name_returns_422(self, client, H, auth_a):
        resp = await client.patch(
            f"{BASE}/{H['cat_a'].id}",
            json={"name": ""},
            headers=auth_a,
        )
        assert resp.status_code == 422


# ── POST /categories/{id}/activate  &  /deactivate ──────────────────────────

class TestActivateDeactivate:

    @pytest.mark.asyncio
    async def test_deactivate_returns_200_and_is_active_false(
        self, client, H, auth_a
    ):
        resp = await client.post(
            f"{BASE}/{H['cat_a'].id}/deactivate", headers=auth_a
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    @pytest.mark.asyncio
    async def test_activate_returns_200_and_is_active_true(
        self, client, H, auth_a
    ):
        await client.post(f"{BASE}/{H['cat_a'].id}/deactivate", headers=auth_a)
        resp = await client.post(
            f"{BASE}/{H['cat_a'].id}/activate", headers=auth_a
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is True

    @pytest.mark.asyncio
    async def test_deactivate_other_tenant_returns_404(self, client, H, auth_a):
        resp = await client.post(
            f"{BASE}/{H['cat_b'].id}/deactivate", headers=auth_a
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_activate_other_tenant_returns_404(self, client, H, auth_a):
        resp = await client.post(
            f"{BASE}/{H['cat_b'].id}/activate", headers=auth_a
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_deactivate_without_token_returns_401(self, client, H):
        resp = await client.post(f"{BASE}/{H['cat_a'].id}/deactivate")
        assert resp.status_code == 401


# ── DELETE /categories/{id} ─────────────────────────────────────────────────

class TestDeleteCategory:

    @pytest.mark.asyncio
    async def test_delete_returns_200_with_message(self, client, H, auth_a):
        # Create a fresh category so deleting it doesn't break other tests
        create = await client.post(
            BASE + "/",
            json={"name": "To Be Deleted"},
            headers=auth_a,
        )
        cat_id = create.json()["id"]

        resp = await client.delete(f"{BASE}/{cat_id}", headers=auth_a)
        assert resp.status_code == 200
        assert "deleted" in resp.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_deleted_category_returns_404_on_get(self, client, H, auth_a):
        create = await client.post(
            BASE + "/",
            json={"name": "Ephemeral"},
            headers=auth_a,
        )
        cat_id = create.json()["id"]

        await client.delete(f"{BASE}/{cat_id}", headers=auth_a)

        resp = await client.get(f"{BASE}/{cat_id}", headers=auth_a)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_other_tenant_returns_404(self, client, H, auth_a):
        resp = await client.delete(f"{BASE}/{H['cat_b'].id}", headers=auth_a)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_404(self, client, H, auth_a):
        from uuid import uuid4
        resp = await client.delete(f"{BASE}/{uuid4()}", headers=auth_a)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_without_token_returns_401(self, client, H):
        resp = await client.delete(f"{BASE}/{H['cat_a'].id}")
        assert resp.status_code == 401
