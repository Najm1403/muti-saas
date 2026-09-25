# tests/test_platform_rbac.py
#
# Coarse platform-admin roles (owner / manager / viewer):
#   1. _normalise_role resolves the (role, is_super) pair
#   2. block_readonly_writes 403s a viewer on writes, passes reads + non-viewers

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from api.platform.dependencies import CurrentPlatformAdmin, block_readonly_writes
from api.platform.platform_admins import _normalise_role
from core.exceptions import ForbiddenError


# ── 1. role / is_super normalisation ─────────────────────────

class TestNormaliseRole:
    def test_role_owner_implies_super(self):
        assert _normalise_role("owner", None) == ("owner", True)

    def test_role_manager_not_super(self):
        assert _normalise_role("manager", None) == ("manager", False)

    def test_role_viewer_not_super(self):
        assert _normalise_role("viewer", None) == ("viewer", False)

    def test_legacy_is_super_true_maps_to_owner(self):
        assert _normalise_role(None, True) == ("owner", True)

    def test_legacy_is_super_false_maps_to_manager(self):
        assert _normalise_role(None, False) == ("manager", False)

    def test_role_wins_over_legacy_flag(self):
        assert _normalise_role("viewer", True) == ("viewer", False)

    def test_default_is_manager(self):
        assert _normalise_role(None, None) == ("manager", False)


# ── 2. block_readonly_writes ────────────────────────────────

def _req(method: str):
    return SimpleNamespace(method=method)


def _admin(role: str):
    return CurrentPlatformAdmin(admin_id=uuid4(), is_super=(role == "owner"), role=role)


class TestReadonlyGuard:
    @pytest.mark.asyncio
    async def test_viewer_blocked_on_write(self):
        for method in ("POST", "PATCH", "PUT", "DELETE"):
            with pytest.raises(ForbiddenError) as ei:
                await block_readonly_writes(_req(method), _admin("viewer"))
            assert ei.value.code == "ROLE_READ_ONLY"

    @pytest.mark.asyncio
    async def test_viewer_allowed_on_read(self):
        for method in ("GET", "HEAD", "OPTIONS"):
            out = await block_readonly_writes(_req(method), _admin("viewer"))
            assert out.role == "viewer"

    @pytest.mark.asyncio
    async def test_manager_and_owner_pass_writes(self):
        for role in ("manager", "owner"):
            out = await block_readonly_writes(_req("POST"), _admin(role))
            assert out.role == role
