from uuid import uuid4

import pytest
from sqlalchemy import select

from api.dependencies import CurrentUser, get_user_permissions, require_tenant_admin
from core.exceptions import ForbiddenError, NotFoundError
from models.permission import Permission
from schemas.role import RoleCreate
from services.role_service import RoleService


async def _permission(db, code: str) -> Permission:
    permission = await db.scalar(select(Permission).where(Permission.code == code))
    if permission is None:
        permission = Permission(
            id=uuid4(), code=code, name=code, module=code.split(".", 1)[0], is_active=True
        )
        db.add(permission)
        await db.flush()
    return permission


@pytest.mark.asyncio
async def test_user_permission_checklist_overrides_only_that_user(db, H):
    service = RoleService(db)
    view = await _permission(db, "sales.view")
    create = await _permission(db, "sales.create")
    role = await service.create(H["tenant_a"].id, RoleCreate(name="Test Cashier"))
    await service.assign_permission(role.id, view.id, H["tenant_a"].id)
    await service.assign_permission(role.id, create.id, H["tenant_a"].id)
    await service.assign_user_role(H["user_a"].id, role.id, H["tenant_a"].id)

    states = await service.list_user_permissions(H["user_a"].id, H["tenant_a"].id)
    by_code = {state.code: state for state in states}
    assert by_code["sales.view"].checked is True
    assert by_code["sales.view"].inherited is True

    await service.replace_user_permissions(
        H["user_a"].id, H["tenant_a"].id, [create.id]
    )
    effective = await get_user_permissions(db, H["user_a"].id, H["tenant_a"].id)
    assert "sales.create" in effective
    assert "sales.view" not in effective

    # The shared role remains unchanged; the override belongs only to this user.
    role_permissions = await service.list_role_permissions(role.id, H["tenant_a"].id)
    assert {permission.id for permission in role_permissions} == {view.id, create.id}


@pytest.mark.asyncio
async def test_user_permissions_are_tenant_scoped_and_admin_edit_is_enforced(db, H):
    service = RoleService(db)
    with pytest.raises(NotFoundError):
        await service.list_user_permissions(H["user_b"].id, H["tenant_a"].id)

    current = CurrentUser(user_id=H["user_a"].id, tenant_id=H["tenant_a"].id)
    with pytest.raises(ForbiddenError):
        await require_tenant_admin(current_user=current, db=db)

    admin = await service.create(H["tenant_a"].id, RoleCreate(name="Admin"))
    await service.assign_user_role(H["user_a"].id, admin.id, H["tenant_a"].id)
    assert await require_tenant_admin(current_user=current, db=db) == current
    with pytest.raises(ForbiddenError):
        await service.replace_user_permissions(H["user_a"].id, H["tenant_a"].id, [])


@pytest.mark.asyncio
async def test_get_user_permissions_endpoint_requires_tenant_admin(db, H):
    """GET /users/{id}/permissions must be gated the same way as the
    sibling PUT — an ordinary users.manage role (not an admin-equivalent
    one) must not be able to read another user's full permission-override
    state, even though it can otherwise manage users."""
    from tests.test_deployment_regressions import call

    service = RoleService(db)
    manage_perm = await _permission(db, "users.manage")
    role = await service.create(H["tenant_a"].id, RoleCreate(name="User Manager"))
    await service.assign_permission(role.id, manage_perm.id, H["tenant_a"].id)
    await service.assign_user_role(H["user_a"].id, role.id, H["tenant_a"].id)

    resp = await call(db, H, "GET", f"/api/v1/users/{H['user_a'].id}/permissions")
    assert resp.status_code == 403, resp.text

    admin_role = await service.create(H["tenant_a"].id, RoleCreate(name="Admin"))
    await service.assign_user_role(H["user_a"].id, admin_role.id, H["tenant_a"].id)
    resp = await call(db, H, "GET", f"/api/v1/users/{H['user_a'].id}/permissions")
    assert resp.status_code == 200, resp.text
