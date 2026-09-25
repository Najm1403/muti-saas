# tests/test_tenant_isolation.py
#
# Verifies that tenant isolation holds at every layer:
#   1. Repository layer  — queries scoped by tenant_id
#   2. JWT layer         — tokens carry correct tenant_id, types are enforced
#   3. Service layer     — login rejects cross-tenant credentials
#   4. Username layer    — same username allowed in different tenants

from __future__ import annotations

import pytest
import pytest_asyncio
from uuid import uuid4

from core.security import (
    create_access_token,
    create_platform_access_token,
    decode_token,
    verify_password,
)
from repositories.user_repository import UserRepository
from repositories.tenant_repository import TenantRepository
from services.auth_service import AuthService
from schemas.auth import LoginRequest


# ================================================================
# 1. REPOSITORY LAYER
# ================================================================

class TestRepositoryIsolation:
    """
    Repository queries must NEVER return data from another tenant,
    even when given a valid ID that exists in a different tenant.
    """

    @pytest.mark.asyncio
    async def test_user_invisible_across_tenants_by_id(self, db, two_tenants):
        """
        Looking up user_a's ID scoped to tenant_b must return None.
        A cross-tenant ID lookup must never succeed.
        """
        repo = UserRepository(db)
        user_a = two_tenants["user_a"]
        tenant_b = two_tenants["tenant_b"]

        result = await repo.get_by_id(id=user_a.id, tenant_id=tenant_b.id)
        assert result is None, (
            f"ISOLATION BREACH: user_a ({user_a.id}) visible from tenant_b ({tenant_b.id})"
        )

    @pytest.mark.asyncio
    async def test_user_invisible_across_tenants_by_username(self, db, two_tenants):
        """
        alice exists in tenant_a. Querying for alice inside tenant_b must return None.
        """
        repo = UserRepository(db)
        tenant_b = two_tenants["tenant_b"]

        result = await repo.get_by_username(username="alice", tenant_id=tenant_b.id)
        assert result is None, "ISOLATION BREACH: alice from tenant_a found inside tenant_b"

    @pytest.mark.asyncio
    async def test_user_list_scoped_to_own_tenant(self, db, two_tenants):
        """
        Listing users for tenant_a must return only tenant_a's users.
        tenant_b's users must never appear.
        """
        repo = UserRepository(db)
        tenant_a = two_tenants["tenant_a"]
        tenant_b = two_tenants["tenant_b"]

        users_a = await repo.list(tenant_id=tenant_a.id)
        user_ids_a = {u.id for u in users_a}

        assert two_tenants["user_a"].id in user_ids_a, "user_a missing from own tenant list"
        assert two_tenants["user_b"].id not in user_ids_a, (
            "ISOLATION BREACH: user_b from tenant_b appeared in tenant_a's user list"
        )

    @pytest.mark.asyncio
    async def test_same_username_allowed_in_different_tenants(self, db, two_tenants):
        """
        The same username can exist in two separate tenants — they are isolated namespaces.
        alice@tenant_a and alice@tenant_b are completely separate users.
        """
        repo = UserRepository(db)
        from core.security import hash_password

        tenant_b = two_tenants["tenant_b"]

        # Create alice in tenant_b as well — should not conflict.
        user_b_alice = await repo.create(
            tenant_id=tenant_b.id,
            username="alice",
            full_name="Alice in Tenant B",
            password_hash=hash_password("different_password"),
        )
        await db.flush()

        alice_in_a = await repo.get_by_username("alice", two_tenants["tenant_a"].id)
        alice_in_b = await repo.get_by_username("alice", tenant_b.id)

        assert alice_in_a is not None
        assert alice_in_b is not None
        assert alice_in_a.id != alice_in_b.id, (
            "ISOLATION BREACH: same username in two tenants resolved to same user"
        )
        assert alice_in_a.tenant_id == two_tenants["tenant_a"].id
        assert alice_in_b.tenant_id == tenant_b.id

    @pytest.mark.asyncio
    async def test_nonexistent_tenant_id_returns_nothing(self, db, two_tenants):
        """
        Querying with a random UUID (no such tenant) must always return empty results.
        """
        repo = UserRepository(db)
        fake_tenant_id = uuid4()

        result = await repo.get_by_id(
            id=two_tenants["user_a"].id,
            tenant_id=fake_tenant_id,
        )
        assert result is None, "ISOLATION BREACH: user found under non-existent tenant ID"

        users = await repo.list(tenant_id=fake_tenant_id)
        assert users == [], "ISOLATION BREACH: users returned for non-existent tenant"


# ================================================================
# 2. JWT LAYER
# ================================================================

class TestJWTIsolation:
    """
    Tokens must carry the correct tenant_id and type.
    Cross-type tokens must be rejected.
    """

    def test_access_token_embeds_correct_tenant_id(self, two_tenants):
        """
        A token created for user_a must carry tenant_a's ID — never tenant_b's.
        """
        user_a = two_tenants["user_a"]
        tenant_a = two_tenants["tenant_a"]
        tenant_b = two_tenants["tenant_b"]

        token = create_access_token(user_a.id, tenant_a.id)
        payload = decode_token(token)

        assert payload["sub"] == str(user_a.id)
        assert payload["tenant_id"] == str(tenant_a.id)
        assert payload["tenant_id"] != str(tenant_b.id), (
            "ISOLATION BREACH: token for user_a contains tenant_b's ID"
        )

    def test_two_users_get_different_tenant_ids_in_token(self, two_tenants):
        """
        Tokens for user_a and user_b must carry different tenant_ids.
        """
        user_a, tenant_a = two_tenants["user_a"], two_tenants["tenant_a"]
        user_b, tenant_b = two_tenants["user_b"], two_tenants["tenant_b"]

        token_a = create_access_token(user_a.id, tenant_a.id)
        token_b = create_access_token(user_b.id, tenant_b.id)

        payload_a = decode_token(token_a)
        payload_b = decode_token(token_b)

        assert payload_a["tenant_id"] != payload_b["tenant_id"], (
            "ISOLATION BREACH: two different tenants produced the same tenant_id in JWT"
        )
        assert payload_a["sub"] != payload_b["sub"]

    def test_tenant_token_type_is_access(self, two_tenants):
        """Tenant tokens must have type='access', not 'platform_access'."""
        user_a = two_tenants["user_a"]
        tenant_a = two_tenants["tenant_a"]
        token = create_access_token(user_a.id, tenant_a.id)
        payload = decode_token(token)
        assert payload["type"] == "access"

    def test_platform_token_has_no_tenant_id(self, two_tenants):
        """
        Platform tokens must NOT carry a tenant_id.
        This prevents a platform token from being used as a tenant token.
        """
        from uuid import uuid4
        fake_admin_id = uuid4()
        token = create_platform_access_token(fake_admin_id)
        payload = decode_token(token)

        assert payload["type"] == "platform_access"
        assert "tenant_id" not in payload, (
            "SECURITY ISSUE: platform token contains tenant_id — cross-use possible"
        )

    def test_platform_token_rejected_as_tenant_token(self, two_tenants):
        """
        A platform_access token presented to a tenant endpoint must be rejected.
        The dependency checks type == 'access', so platform_access fails.
        """
        fake_admin_id = uuid4()
        token = create_platform_access_token(fake_admin_id)
        payload = decode_token(token)

        # Simulate what get_current_user() checks
        assert payload.get("type") != "access", (
            "SECURITY ISSUE: platform token passed as tenant access token"
        )

    def test_tenant_token_rejected_as_platform_token(self, two_tenants):
        """
        A tenant access token presented to a platform endpoint must be rejected.
        The dependency checks type == 'platform_access', so 'access' fails.
        """
        user_a = two_tenants["user_a"]
        tenant_a = two_tenants["tenant_a"]
        token = create_access_token(user_a.id, tenant_a.id)
        payload = decode_token(token)

        assert payload.get("type") != "platform_access", (
            "SECURITY ISSUE: tenant token passed as platform access token"
        )


# ================================================================
# 3. SERVICE / LOGIN LAYER
# ================================================================

class TestLoginIsolation:
    """
    Login must scope credentials to a specific tenant.
    User from tenant_a cannot log in using tenant_b's code and vice versa.
    """

    @pytest.mark.asyncio
    async def test_correct_credentials_succeed(self, db, two_tenants):
        """Baseline: correct credentials for each tenant must work."""
        svc = AuthService(db)
        password = two_tenants["password"]

        token_a = await svc.login(LoginRequest(
            tenant_code="ALPHA_TEST",
            username="alice",
            password=password,
        ))
        assert token_a.access_token

        token_b = await svc.login(LoginRequest(
            tenant_code="BETA_TEST",
            username="bob",
            password=password,
        ))
        assert token_b.access_token

    @pytest.mark.asyncio
    async def test_wrong_tenant_code_rejected(self, db, two_tenants):
        """
        Alice belongs to ALPHA_TEST. Logging in with BETA_TEST + alice must fail.
        """
        from core.exceptions import AuthenticationError
        svc = AuthService(db)

        with pytest.raises(AuthenticationError):
            await svc.login(LoginRequest(
                tenant_code="BETA_TEST",
                username="alice",
                password=two_tenants["password"],
            ))

    @pytest.mark.asyncio
    async def test_wrong_password_rejected(self, db, two_tenants):
        """Correct tenant + wrong password must be rejected."""
        from core.exceptions import AuthenticationError
        svc = AuthService(db)

        with pytest.raises(AuthenticationError):
            await svc.login(LoginRequest(
                tenant_code="ALPHA_TEST",
                username="alice",
                password="wrong_password",
            ))

    @pytest.mark.asyncio
    async def test_login_token_contains_correct_tenant(self, db, two_tenants):
        """
        Token issued after login must embed the correct tenant_id,
        not any other tenant's ID.
        """
        svc = AuthService(db)
        result = await svc.login(LoginRequest(
            tenant_code="ALPHA_TEST",
            username="alice",
            password=two_tenants["password"],
        ))

        payload = decode_token(result.access_token)
        assert payload["tenant_id"] == str(two_tenants["tenant_a"].id), (
            "ISOLATION BREACH: login token for alice contains wrong tenant_id"
        )
        assert payload["tenant_id"] != str(two_tenants["tenant_b"].id)

    @pytest.mark.asyncio
    async def test_inactive_tenant_blocks_all_users(self, db, two_tenants):
        """
        Deactivating tenant_a must block alice from logging in,
        while bob (tenant_b) is completely unaffected.
        """
        from core.exceptions import ForbiddenError
        from repositories.tenant_repository import TenantRepository

        tenant_repo = TenantRepository(db)
        svc = AuthService(db)

        # Deactivate tenant_a directly via update
        await tenant_repo.update(two_tenants["tenant_a"].id, is_active=False)
        await db.flush()

        # Alice (tenant_a) must be blocked
        with pytest.raises(ForbiddenError):
            await svc.login(LoginRequest(
                tenant_code="ALPHA_TEST",
                username="alice",
                password=two_tenants["password"],
            ))

        # Bob (tenant_b) must still work fine
        token_b = await svc.login(LoginRequest(
            tenant_code="BETA_TEST",
            username="bob",
            password=two_tenants["password"],
        ))
        assert token_b.access_token, "Bob should still log in — his tenant is active"


# ================================================================
# 4. PASSWORD ISOLATION
# ================================================================

class TestPasswordIsolation:
    """Passwords are hashed and never shared across tenants."""

    @pytest.mark.asyncio
    async def test_passwords_stored_as_hashes(self, db, two_tenants):
        """Raw passwords must never be stored — only bcrypt hashes."""
        user_a = two_tenants["user_a"]
        user_b = two_tenants["user_b"]
        password = two_tenants["password"]

        assert user_a.password_hash != password, "SECURITY: plain-text password stored!"
        assert user_b.password_hash != password, "SECURITY: plain-text password stored!"
        assert user_a.password_hash.startswith("$2"), "Expected bcrypt hash for user_a"
        assert user_b.password_hash.startswith("$2"), "Expected bcrypt hash for user_b"

    def test_same_password_produces_different_hashes(self, two_tenants):
        """
        bcrypt salts every hash independently — calling hash_password twice
        with the same input must produce two different strings.
        """
        from core.security import hash_password
        password = two_tenants["password"]

        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2, (
            "SECURITY: bcrypt produced identical hashes for the same password — no salt?"
        )
        # Both must still verify correctly against the original password.
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

    @pytest.mark.asyncio
    async def test_password_verifies_correctly(self, db, two_tenants):
        """verify_password must work for each user independently."""
        password = two_tenants["password"]
        user_a = two_tenants["user_a"]
        user_b = two_tenants["user_b"]

        assert verify_password(password, user_a.password_hash)
        assert verify_password(password, user_b.password_hash)

        # Cross-verify must also be True (same password, different hash — bcrypt handles it)
        assert verify_password(password, user_b.password_hash)
