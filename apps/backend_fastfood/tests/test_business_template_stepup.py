# tests/test_business_template_stepup.py
#
# Two independent guards on Business Template delete / config.modules.hidden
# changes, required together (see BUSINESS_TEMPLATE_GUIDE.md):
#   1. require_business_template_manage() — an explicit, grantable permission
#      (PlatformAdmin.can_manage_business_templates); owners always qualify.
#   2. require_step_up() / optional_step_up() — a fresh, action+template-scoped
#      password re-confirmation (POST /auth/step-up), on top of (never instead
#      of) the permission check.

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
import pytest_asyncio

from api.platform.dependencies import (
    CurrentPlatformAdmin,
    optional_step_up,
    require_business_template_manage,
    require_step_up,
)
from core.exceptions import AuthenticationError, ForbiddenError, ValidationError
from core.security import create_platform_step_up_token, hash_password
from models.business_template import BusinessTemplate
from models.platform_admin import PlatformAdmin
from schemas.business_template import BusinessTemplateCreate, BusinessTemplateUpdate
from schemas.platform_auth import PlatformStepUpRequest
from services.business_template_service import BusinessTemplateService
from services.platform_auth_service import PlatformAuthService


def _req(token: str | None):
    return SimpleNamespace(headers={"X-Step-Up-Token": token} if token else {})


# ── 1. require_business_template_manage ─────────────────────

class TestRequireBusinessTemplateManage:
    def test_owner_always_qualifies(self):
        admin = CurrentPlatformAdmin(admin_id=uuid4(), is_super=True, role="owner")
        assert require_business_template_manage(admin) is admin

    def test_manager_without_flag_blocked(self):
        admin = CurrentPlatformAdmin(admin_id=uuid4(), is_super=False, role="manager")
        with pytest.raises(ForbiddenError) as ei:
            require_business_template_manage(admin)
        assert ei.value.code == "BUSINESS_TEMPLATE_MANAGE_REQUIRED"

    def test_manager_with_flag_qualifies(self):
        admin = CurrentPlatformAdmin(
            admin_id=uuid4(), is_super=False, role="manager",
            can_manage_business_templates=True,
        )
        assert require_business_template_manage(admin) is admin


# ── 2. step-up token validation ──────────────────────────────

class TestStepUpValidation:
    @pytest.mark.asyncio
    async def test_valid_token_passes(self):
        admin_id, tpl_id = uuid4(), uuid4()
        admin = CurrentPlatformAdmin(admin_id=admin_id, is_super=True, role="owner")
        token = create_platform_step_up_token(admin_id, "delete_business_template", tpl_id)
        dep = require_step_up("delete_business_template")
        assert await dep(id=tpl_id, request=_req(token), current=admin) is admin

    @pytest.mark.asyncio
    async def test_missing_token_rejected(self):
        admin = CurrentPlatformAdmin(admin_id=uuid4(), is_super=True, role="owner")
        dep = require_step_up("delete_business_template")
        with pytest.raises(ForbiddenError) as ei:
            await dep(id=uuid4(), request=_req(None), current=admin)
        assert ei.value.code == "STEP_UP_REQUIRED"

    @pytest.mark.asyncio
    async def test_wrong_action_rejected(self):
        admin_id, tpl_id = uuid4(), uuid4()
        admin = CurrentPlatformAdmin(admin_id=admin_id, is_super=True, role="owner")
        # Token minted for a modules-update, presented to the delete guard.
        token = create_platform_step_up_token(
            admin_id, "update_business_template_modules", tpl_id
        )
        dep = require_step_up("delete_business_template")
        with pytest.raises(ForbiddenError) as ei:
            await dep(id=tpl_id, request=_req(token), current=admin)
        assert ei.value.code == "STEP_UP_REQUIRED"

    @pytest.mark.asyncio
    async def test_wrong_template_rejected(self):
        """A token confirmed for template A must not work against template B."""
        admin_id = uuid4()
        admin = CurrentPlatformAdmin(admin_id=admin_id, is_super=True, role="owner")
        token = create_platform_step_up_token(admin_id, "delete_business_template", uuid4())
        dep = require_step_up("delete_business_template")
        with pytest.raises(ForbiddenError) as ei:
            await dep(id=uuid4(), request=_req(token), current=admin)
        assert ei.value.code == "STEP_UP_REQUIRED"

    @pytest.mark.asyncio
    async def test_wrong_admin_rejected(self):
        """A token minted for one admin must not work when presented by another."""
        tpl_id = uuid4()
        token = create_platform_step_up_token(uuid4(), "delete_business_template", tpl_id)
        other_admin = CurrentPlatformAdmin(admin_id=uuid4(), is_super=True, role="owner")
        dep = require_step_up("delete_business_template")
        with pytest.raises(ForbiddenError) as ei:
            await dep(id=tpl_id, request=_req(token), current=other_admin)
        assert ei.value.code == "STEP_UP_REQUIRED"

    @pytest.mark.asyncio
    async def test_optional_step_up_returns_bool_not_raise(self):
        admin = CurrentPlatformAdmin(admin_id=uuid4(), is_super=True, role="owner")
        assert await optional_step_up(id=uuid4(), request=_req(None), current=admin) is False

        admin_id, tpl_id = uuid4(), uuid4()
        admin2 = CurrentPlatformAdmin(admin_id=admin_id, is_super=True, role="owner")
        token = create_platform_step_up_token(
            admin_id, "update_business_template_modules", tpl_id
        )
        assert await optional_step_up(id=tpl_id, request=_req(token), current=admin2) is True


# ── 3. PlatformAuthService.step_up() — password re-verification ──

@pytest_asyncio.fixture
async def platform_admin(db):
    admin = PlatformAdmin(
        id=uuid4(), email=f"{uuid4().hex[:8]}@example.com", full_name="Test Admin",
        password_hash=hash_password("Correct-Horse-1"), is_active=True,
        is_super=False, role="manager",
    )
    db.add(admin)
    await db.flush()
    return admin


class TestStepUpService:
    @pytest.mark.asyncio
    async def test_wrong_password_rejected(self, db, platform_admin):
        with pytest.raises(AuthenticationError):
            await PlatformAuthService(db).step_up(
                platform_admin.id,
                PlatformStepUpRequest(
                    password="nope", action="delete_business_template",
                    template_id=uuid4(),
                ),
            )

    @pytest.mark.asyncio
    async def test_correct_password_issues_scoped_token(self, db, platform_admin):
        tpl_id = uuid4()
        resp = await PlatformAuthService(db).step_up(
            platform_admin.id,
            PlatformStepUpRequest(
                password="Correct-Horse-1", action="delete_business_template",
                template_id=tpl_id,
            ),
        )
        assert resp.step_up_token
        assert resp.expires_in == 5 * 60
        # The issued token must actually validate against the same action/template.
        admin = CurrentPlatformAdmin(admin_id=platform_admin.id, is_super=False, role="manager")
        dep = require_step_up("delete_business_template")
        assert await dep(id=tpl_id, request=_req(resp.step_up_token), current=admin) is admin


# ── 4. BusinessTemplateService.update() — conditional step-up enforcement ──

class TestServiceModulesStepUp:
    @pytest.mark.asyncio
    async def test_template_can_seed_color_as_variant_group(self, db):
        # Colors now join the same shareable Variant Option Group mechanism
        # as RAM/Storage — a template may freely seed a "Color" group.
        config = {"variants": {"seed_groups": [{"name": "Color", "values": ["Black"]}]}}
        created = await BusinessTemplateService(db).create(
            BusinessTemplateCreate(name=f"Valid {uuid4().hex[:8]}", config=config)
        )
        assert created.config["variants"]["seed_groups"][0]["name"] == "Color"

    @pytest.mark.asyncio
    async def test_non_modules_change_needs_no_step_up(self, db, business_template: BusinessTemplate):
        result = await BusinessTemplateService(db).update(
            business_template.id,
            BusinessTemplateUpdate(config={**business_template.config, "pricing": {"show_cost_price": True}}),
            step_up_ok=False,
        )
        assert result.config["pricing"]["show_cost_price"] is True

    @pytest.mark.asyncio
    async def test_modules_change_blocked_without_step_up(self, db, business_template: BusinessTemplate):
        with pytest.raises(ForbiddenError) as ei:
            await BusinessTemplateService(db).update(
                business_template.id,
                BusinessTemplateUpdate(config={**business_template.config, "modules": {"hidden": ["kitchen"]}}),
                step_up_ok=False,
            )
        assert ei.value.code == "STEP_UP_REQUIRED"

    @pytest.mark.asyncio
    async def test_modules_change_succeeds_with_step_up(self, db, business_template: BusinessTemplate):
        result = await BusinessTemplateService(db).update(
            business_template.id,
            BusinessTemplateUpdate(config={**business_template.config, "modules": {"hidden": ["kitchen"]}}),
            step_up_ok=True,
        )
        assert result.config["modules"]["hidden"] == ["kitchen"]

    @pytest.mark.asyncio
    async def test_setting_modules_to_same_value_needs_no_step_up(self, db, business_template: BusinessTemplate):
        """Re-saving the identical hidden list (e.g. editing an unrelated field
        in the same request) must not spuriously demand a step-up."""
        cfg = {**business_template.config, "modules": {"hidden": ["kitchen"]}}
        await BusinessTemplateService(db).update(
            business_template.id, BusinessTemplateUpdate(config=cfg), step_up_ok=True,
        )
        # Same hidden list again, no step-up this time — must succeed.
        result = await BusinessTemplateService(db).update(
            business_template.id,
            BusinessTemplateUpdate(config={**cfg, "pricing": {"require_cost_price": True}}),
            step_up_ok=False,
        )
        assert result.config["modules"]["hidden"] == ["kitchen"]


# ── 5. Only a super admin can grant/revoke the capability itself ──

class TestGrantingTheCapabilityIsSuperOnly:
    @pytest.mark.asyncio
    async def test_manager_cannot_grant_it_to_self(self, db, platform_admin):
        from api.platform.platform_admins import update_platform_admin
        from repositories.platform_admin_repository import PlatformAdminRepository
        from schemas.platform_auth import PlatformAdminUpdate

        current = CurrentPlatformAdmin(admin_id=platform_admin.id, is_super=False, role="manager")
        with pytest.raises(ForbiddenError):
            await update_platform_admin(
                id=platform_admin.id,
                data=PlatformAdminUpdate(can_manage_business_templates=True),
                current=current,
                repo=PlatformAdminRepository(db),
                db=db,
            )

    @pytest.mark.asyncio
    async def test_owner_can_grant_it(self, db, platform_admin):
        from api.platform.platform_admins import update_platform_admin
        from repositories.platform_admin_repository import PlatformAdminRepository
        from schemas.platform_auth import PlatformAdminUpdate

        owner = CurrentPlatformAdmin(admin_id=uuid4(), is_super=True, role="owner")
        result = await update_platform_admin(
            id=platform_admin.id,
            data=PlatformAdminUpdate(can_manage_business_templates=True),
            current=owner,
            repo=PlatformAdminRepository(db),
            db=db,
        )
        assert result.can_manage_business_templates is True
