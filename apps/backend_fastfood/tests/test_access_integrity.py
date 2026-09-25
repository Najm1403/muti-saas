"""End-to-end integrity checks for tenant, role, module, and platform boundaries."""

from uuid import uuid4

import pytest
from fastapi.security import HTTPAuthorizationCredentials

from api.dependencies import get_current_user, get_user_permissions, tenant_enabled_modules
from api.platform.dependencies import get_current_platform_admin
from core.exceptions import AuthenticationError, NotFoundError
from core.security import create_access_token, create_platform_access_token
from models.business_template import BusinessTemplate
from models.role import Role
from models.user_role import UserRole
from services.role_service import RoleService


def bearer(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


@pytest.mark.asyncio
async def test_signed_token_cannot_claim_another_tenant(db, two_tenants):
    """Even a correctly signed token is invalid when user and tenant disagree."""
    forged = create_access_token(
        two_tenants["user_a"].id,
        two_tenants["tenant_b"].id,
    )

    with pytest.raises(AuthenticationError):
        await get_current_user(credentials=bearer(forged), db=db)


@pytest.mark.asyncio
async def test_platform_and_tenant_tokens_cannot_cross_auth_boundaries(db, two_tenants):
    tenant_token = create_access_token(
        two_tenants["user_a"].id,
        two_tenants["tenant_a"].id,
    )
    platform_token = create_platform_access_token(uuid4())

    with pytest.raises(AuthenticationError):
        await get_current_platform_admin(credentials=bearer(tenant_token), db=db)
    with pytest.raises(AuthenticationError):
        await get_current_user(credentials=bearer(platform_token), db=db)


@pytest.mark.asyncio
async def test_foreign_admin_role_link_cannot_grant_permissions(db, two_tenants):
    """A corrupt cross-tenant UserRole row must never activate the admin bypass."""
    foreign_admin = Role(
        id=uuid4(),
        tenant_id=two_tenants["tenant_b"].id,
        name="Admin",
        is_active=True,
    )
    db.add(foreign_admin)
    await db.flush()
    db.add(UserRole(id=uuid4(), user_id=two_tenants["user_a"].id, role_id=foreign_admin.id))
    await db.flush()

    permissions = await get_user_permissions(
        db,
        two_tenants["user_a"].id,
        two_tenants["tenant_a"].id,
    )
    assert permissions == set()


@pytest.mark.asyncio
async def test_role_service_rejects_cross_tenant_user_role_assignments(db, two_tenants):
    role_b = Role(
        id=uuid4(),
        tenant_id=two_tenants["tenant_b"].id,
        name="Tenant B Manager",
        is_active=True,
    )
    db.add(role_b)
    await db.flush()
    service = RoleService(db)

    with pytest.raises(NotFoundError):
        await service.assign_user_role(
            two_tenants["user_a"].id,
            role_b.id,
            two_tenants["tenant_a"].id,
        )
    with pytest.raises(NotFoundError):
        await service.assign_user_role(
            two_tenants["user_a"].id,
            role_b.id,
            two_tenants["tenant_b"].id,
        )


@pytest.mark.asyncio
async def test_business_template_modules_are_isolated_per_tenant(db, two_tenants, business_template):
    restricted_config = dict(business_template.config or {})
    restricted_config["modules"] = {"hidden": ["inventory", "kitchen"]}
    business_template.config = restricted_config

    open_template = BusinessTemplate(
        id=uuid4(),
        name=f"Open {uuid4().hex[:8]}",
        config={"modules": {"hidden": []}},
    )
    db.add(open_template)
    two_tenants["tenant_b"].business_template_id = open_template.id
    await db.flush()

    tenant_a_modules = await tenant_enabled_modules(db, two_tenants["tenant_a"].id)
    tenant_b_modules = await tenant_enabled_modules(db, two_tenants["tenant_b"].id)

    assert "inventory" not in tenant_a_modules
    assert "kitchen" not in tenant_a_modules
    assert "inventory" in tenant_b_modules
    assert "kitchen" in tenant_b_modules
    assert "settings" in tenant_a_modules and "settings" in tenant_b_modules
