# tests/test_module_templates.py
#
# Tenant-dashboard module visibility — folded into BusinessTemplate.config
# (config.modules.hidden), replacing the old standalone Module Template
# system:
#   1. core/modules helpers (mandatory keys, hidden-list normalisation, the
#      effective visible set)
#   2. enforce_module_hidden_list() — validates a hidden list before it's
#      saved onto a template (rejects unknown/mandatory keys)
#   3. tenant_enabled_modules() — resolves a tenant's visible set from its
#      Business Template
#   4. require_module() dependency — 403 MODULE_DISABLED when hidden, pass
#      when visible / unrestricted

from __future__ import annotations
from datetime import datetime, timezone
from starlette.requests import Request

from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select

from api.dependencies import CurrentUser, require_module, tenant_enabled_modules
from core.exceptions import ForbiddenError, ValidationError
from core.modules import (
    MANDATORY_MODULES,
    MODULE_KEYS,
    effective_modules_from_hidden,
    normalise_hidden_modules,
)
from models.business_template import BusinessTemplate
from models.tenant import Tenant
from services.business_policy import business_feature_flags, enforce_module_hidden_list


# ── 1. helpers ──────────────────────────────────────────────

class TestModuleHelpers:
    def test_mandatory_never_hidden(self):
        assert normalise_hidden_modules(["dashboard", "sales"]) == ["sales"]
        assert normalise_hidden_modules(["settings", "subscription"]) == []

    def test_unknown_keys_dropped_order_preserved(self):
        out = normalise_hidden_modules(["reports", "bogus", "sales"])
        assert "bogus" not in out
        assert out == [k for k in MODULE_KEYS if k in out]  # catalog order

    def test_effective_empty_hidden_is_all(self):
        assert effective_modules_from_hidden(None) == set(MODULE_KEYS)
        assert effective_modules_from_hidden([]) == set(MODULE_KEYS)

    def test_effective_restricted(self):
        eff = effective_modules_from_hidden(["kitchen", "expenses"])
        assert "kitchen" not in eff
        assert "expenses" not in eff
        assert MANDATORY_MODULES <= eff
        assert "sales" in eff

    def test_business_feature_flags_are_explicit_and_backward_compatible(self):
        assert business_feature_flags({"addons": {"enabled": False}}) == {
            "variants": True,
            "addons": False,
        }
        assert business_feature_flags({}) == {"variants": True, "addons": True}


# ── 2. save-time validation ───────────────────────────────

class TestEnforceModuleHiddenList:
    def test_empty_ok(self):
        enforce_module_hidden_list([])
        enforce_module_hidden_list(None)

    def test_unknown_key_rejected(self):
        with pytest.raises(ValidationError):
            enforce_module_hidden_list(["bogus"])

    def test_mandatory_key_rejected(self):
        with pytest.raises(ValidationError):
            enforce_module_hidden_list(["settings"])

    def test_valid_optional_keys_ok(self):
        enforce_module_hidden_list(["kitchen", "promotions"])


# ── 3 & 4. tenant_enabled_modules() + require_module() ────

@pytest_asyncio.fixture
async def tenant(db, business_template: BusinessTemplate):
    t = Tenant(id=uuid4(), name="Mod Co", tenant_code="MODCO_T", is_active=True,
               business_template_id=business_template.id)
    db.add(t)
    await db.flush()
    return t


class TestTenantEnabledModules:
    @pytest.mark.asyncio
    async def test_default_is_all(self, db, tenant):
        assert await tenant_enabled_modules(db, tenant.id) == set(MODULE_KEYS)

    @pytest.mark.asyncio
    async def test_hidden_list_restricts(self, db, tenant, business_template):
        business_template.config = {**business_template.config, "modules": {"hidden": ["kitchen", "sales"]}}
        await db.flush()
        eff = await tenant_enabled_modules(db, tenant.id)
        assert "kitchen" not in eff
        assert "sales" not in eff
        assert "menu" in eff
        assert MANDATORY_MODULES <= eff

    @pytest.mark.asyncio
    async def test_every_tenant_on_template_shares_visibility(self, db, business_template):
        """Two tenants on the same Business Template must see the same
        modules — there is no more per-tenant override, by design."""
        business_template.config = {**business_template.config, "modules": {"hidden": ["reports"]}}
        await db.flush()
        t1 = Tenant(id=uuid4(), name="A", tenant_code="A1", is_active=True,
                    business_template_id=business_template.id)
        t2 = Tenant(id=uuid4(), name="B", tenant_code="B1", is_active=True,
                    business_template_id=business_template.id)
        db.add_all([t1, t2])
        await db.flush()
        assert await tenant_enabled_modules(db, t1.id) == await tenant_enabled_modules(db, t2.id)
        assert "reports" not in await tenant_enabled_modules(db, t1.id)


class TestRequireModule:
    async def _grant_admin(self, db, tenant, user):
        from models.role import Role
        from models.user_role import UserRole
        role = Role(id=uuid4(), tenant_id=tenant.id, name="Admin", is_active=True)
        db.add_all([role, UserRole(id=uuid4(), user_id=user.id, role_id=role.id)])
        await db.flush()

    @pytest.mark.asyncio
    async def test_read_permission_grant_and_revocation(self, db, tenant):
        from models.user import User
        from models.role import Role
        from models.user_role import UserRole
        from models.permission import Permission
        from models.role_permission import RolePermission

        user = User(id=uuid4(), tenant_id=tenant.id, username="read-limited",
                    full_name="Read Limited", password_hash="unused", is_active=True,
                    all_branches=True)
        role = Role(id=uuid4(), tenant_id=tenant.id, name="Read Limited", is_active=True)
        db.add_all([user, role]); await db.flush()
        db.add(UserRole(id=uuid4(), user_id=user.id, role_id=role.id))
        permission = await db.scalar(select(Permission).where(Permission.code == "sales.view"))
        if permission is None:
            permission = Permission(id=uuid4(), code="sales.view", name="View Sales",
                                    module="sales", is_active=True)
            db.add(permission)
        await db.flush()
        request = Request({"type": "http", "method": "GET", "path": "/api/v1/sales/", "headers": []})
        current = CurrentUser(user.id, tenant.id)
        with pytest.raises(ForbiddenError) as denied:
            await require_module("sales")(request=request, current_user=current, db=db)
        assert denied.value.code == "PERMISSION_DENIED"

        grant = RolePermission(id=uuid4(), role_id=role.id, permission_id=permission.id)
        db.add(grant); await db.flush()
        assert await require_module("sales")(request=request, current_user=current, db=db) == current

        grant.deleted_at = datetime.now(timezone.utc)
        await db.flush()
        with pytest.raises(ForbiddenError):
            await require_module("sales")(request=request, current_user=current, db=db)

    @pytest.mark.asyncio
    async def test_unrestricted_tenant_passes(self, db, tenant):
        from models.user import User
        user = User(id=uuid4(),tenant_id=tenant.id,username="module-admin",full_name="Module Admin",password_hash="unused",is_active=True,all_branches=True)
        db.add(user); await db.flush(); await self._grant_admin(db, tenant, user)
        cu = CurrentUser(user_id=user.id, tenant_id=tenant.id)
        assert (await require_module("kitchen")(current_user=cu, db=db, request=Request({"type":"http", "method":"GET", "path":"/"}))) is cu

    @pytest.mark.asyncio
    async def test_disabled_module_403(self, db, tenant, business_template):
        business_template.config = {**business_template.config, "modules": {"hidden": ["kitchen"]}}
        await db.flush()
        from models.user import User
        user = User(id=uuid4(),tenant_id=tenant.id,username="module-admin",full_name="Module Admin",password_hash="unused",is_active=True,all_branches=True)
        db.add(user); await db.flush(); await self._grant_admin(db, tenant, user)
        cu = CurrentUser(user_id=user.id, tenant_id=tenant.id)
        # not-hidden one still passes
        assert (await require_module("sales")(current_user=cu, db=db, request=Request({"type":"http", "method":"GET", "path":"/"}))) is cu
        # hidden one is blocked
        with pytest.raises(ForbiddenError) as ei:
            await require_module("kitchen")(current_user=cu, db=db, request=Request({"type":"http", "method":"GET", "path":"/"}))
        assert ei.value.code == "MODULE_DISABLED"

    @pytest.mark.asyncio
    async def test_mandatory_module_always_passes(self, db, tenant, business_template):
        business_template.config = {**business_template.config, "modules": {"hidden": ["sales"]}}
        await db.flush()
        from models.user import User
        user = User(id=uuid4(),tenant_id=tenant.id,username="module-admin",full_name="Module Admin",password_hash="unused",is_active=True,all_branches=True)
        db.add(user); await db.flush(); await self._grant_admin(db, tenant, user)
        cu = CurrentUser(user_id=user.id, tenant_id=tenant.id)
        assert (await require_module("settings")(current_user=cu, db=db, request=Request({"type":"http", "method":"GET", "path":"/"}))) is cu
