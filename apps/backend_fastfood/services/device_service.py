# services/device_service.py
#
# Tenant-owned POS device management.
#
#   Tenant → Business → Branch → Device
#
# The tenant creates a device (name + branch + purpose); the service returns a
# one-time 4-digit activation code (15-min TTL). A physical device pairs itself by
# POSTing that code to /api/v1/pos/auth/activate.
#
# Lifecycle (models.device.DeviceStatus): PENDING → ACTIVE → SUSPENDED ⇄ ACTIVE, → REVOKED.
# A PLATFORM suspension cannot be lifted by the tenant.

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ConflictError, NotFoundError, ValidationError
from models.branch import Branch
from models.device import Device, DeviceStatus, SuspendScope
from models.business import Business
from models.tenant import Tenant
from repositories.branch_repository import BranchRepository
from repositories.device_repository import DeviceRepository
from repositories.subscription_repository import SubscriptionRepository
from schemas.device import (
    ActivationCodeView,
    DeviceCreate,
    DeviceCreatedResponse,
    DeviceListItem,
    DeviceResponse,
    DeviceUpdate,
)
from services.device_sync_service import _sync_status

_ACTIVATION_TTL = timedelta(minutes=15)
_NO_PLAN_DEVICE_ALLOWANCE = 1  # devices a tenant may create without an active subscription


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def _normalise_code(raw: str) -> str:
    """'583 291' / '583-291' → '583291'."""
    return "".join(ch for ch in raw if ch.isdigit())


def _letter_for_index(n: int) -> str:
    """0->A, 1->B, ..., 25->Z, 26->AA, 27->AB, ... (spreadsheet column style)."""
    n += 1
    letters = ""
    while n > 0:
        n, rem = divmod(n - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


class DeviceService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = DeviceRepository(db)
        self.branch_repo = BranchRepository(db)
        self.sub_repo = SubscriptionRepository(db)

    # ── helpers ─────────────────────────────────────────────────────────

    async def _verify_branch(self, branch_id: UUID, tenant_id: UUID) -> None:
        if not await self.branch_repo.get_by_id(branch_id, tenant_id):
            raise NotFoundError("Branch not found.")

    async def _device_limit(self, tenant_id: UUID) -> int:
        """-1 = unlimited. No active subscription → a small grace allowance."""
        sub = await self.sub_repo.get_active_for_tenant(tenant_id)
        if sub and sub.plan:
            return sub.plan.max_devices
        return _NO_PLAN_DEVICE_ALLOWANCE

    def _issue_code(self, device: Device) -> str:
        code = f"{secrets.randbelow(10_000):04d}"
        device.activation_code_hash = _hash_code(code)
        device.activation_code = code  # plaintext, re-displayable until consumed
        device.activation_code_expires_at = datetime.now(timezone.utc) + _ACTIVATION_TTL
        device.activation_code_used_at = None
        return code

    def _created(self, device: Device, code: str) -> DeviceCreatedResponse:
        data = DeviceResponse.model_validate(device).model_dump()
        data.pop("activation_code_expires_at", None)
        return DeviceCreatedResponse(
            **data,
            activation_code=code,
            activation_code_expires_at=device.activation_code_expires_at,
        )

    # ── create / regenerate code ───────────────────────────────────────

    async def create(
        self, tenant_id: UUID, data: DeviceCreate
    ) -> DeviceCreatedResponse:
        await self._verify_branch(data.branch_id, tenant_id)

        # Locks the tenant row so two concurrent "Create Device" requests
        # can't both pass the plan's device-limit check before either
        # commits (the same class of race services/plan_quota_service.py
        # closes for branches), and the branch row so two concurrent
        # creates for the same branch can't compute the same next device
        # letter — both counts below are read-then-act, so without these
        # locks two overlapping transactions can both see the same "count
        # so far" and both win. A DB-level uq_device_branch_letter unique
        # constraint (models/device.py's __table_args__) backstops the
        # letter case even if this lock is ever bypassed by a future code
        # path.
        tenant = await self.db.scalar(
            select(Tenant).where(Tenant.id == tenant_id, Tenant.deleted_at.is_(None))
            .with_for_update()
        )
        if not tenant:
            raise NotFoundError("Tenant not found.")
        await self.db.scalar(
            select(Branch.id).where(Branch.id == data.branch_id).with_for_update()
        )

        limit = await self._device_limit(tenant_id)
        if limit != -1:
            used = await self.repo.count_billable_for_tenant(tenant_id)
            if used >= limit:
                raise ConflictError(
                    f"Device limit reached ({limit}). Upgrade your plan to add more devices."
                )

        device_code = f"POS-{secrets.token_hex(3).upper()}"
        letter = _letter_for_index(await self.repo.count_all_for_branch(data.branch_id))
        try:
            device = await self.repo.create(
                branch_id=data.branch_id,
                tenant_id=tenant_id,
                device_code=device_code,
                letter=letter,
                name=data.name.strip(),
                device_type=data.device_type,
            )
        except ValueError as exc:  # pragma: no cover - random collision
            raise ConflictError(str(exc)) from exc
        except IntegrityError as exc:  # pragma: no cover - defense in depth; the
            # branch-row lock above should already make this unreachable
            await self.db.rollback()
            raise ConflictError(
                "This device's letter or code was just taken by another request. Try again."
            ) from exc

        code = self._issue_code(device)
        await self.db.commit()
        await self.db.refresh(device)
        return self._created(device, code)

    async def regenerate_code(self, id: UUID, tenant_id: UUID) -> DeviceCreatedResponse:
        device = await self.repo.get_by_id(id, tenant_id)
        if not device:
            raise NotFoundError("Device not found.")
        if device.status == DeviceStatus.REVOKED:
            raise ValidationError("Cannot issue a code for a revoked device.")
        if device.activated_at is not None:
            raise ConflictError(
                "This device is already activated. Use “Reset device” to unpair it "
                "before pairing a different device."
            )
        code = self._issue_code(device)
        await self.db.commit()
        await self.db.refresh(device)
        return self._created(device, code)

    async def get_code(self, id: UUID, tenant_id: UUID) -> ActivationCodeView:
        """Re-show the current pending code, or explain why there isn't one."""
        device = await self._get_or_404(id, tenant_id)

        if device.status == DeviceStatus.REVOKED:
            return ActivationCodeView(
                device_id=device.id, status=device.status,
                expired=False, used=False, can_regenerate=False,
            )
        if device.activated_at is not None:
            # Already paired — the code was consumed and must not be shown again.
            return ActivationCodeView(
                device_id=device.id, status=device.status,
                expired=False, used=True, can_regenerate=False,
            )

        now = datetime.now(timezone.utc)
        expired = (
            device.activation_code_hash is None
            or device.activation_code_expires_at is None
            or device.activation_code_expires_at < now
        )
        return ActivationCodeView(
            device_id=device.id,
            status=device.status,
            activation_code=None if expired else device.activation_code,
            activation_code_expires_at=None if expired else device.activation_code_expires_at,
            expired=expired,
            used=False,
            can_regenerate=True,
        )

    async def reset(self, id: UUID, tenant_id: UUID) -> DeviceCreatedResponse:
        """Unpair an activated device and issue a fresh activation code.

        The physical device that was paired stops working the next time it
        reaches the server (status is PENDING again), and can be re-activated —
        by the same or a different device — with the new code. The device keeps
        its slot against the plan limit.
        """
        device = await self._get_or_404(id, tenant_id)
        if device.suspended_scope == SuspendScope.PLATFORM:
            raise ValidationError("Only the platform can restore this suspended device.")
        if device.status == DeviceStatus.REVOKED:
            raise ValidationError("This device has been revoked and cannot be reset.")
        if device.activated_at is None:
            raise ValidationError(
                "This device has not been activated yet — use “Generate new code” instead."
            )
        device.status = DeviceStatus.PENDING
        device.suspended_scope = None
        device.activated_at = None
        device.activation_code_used_at = None
        device.last_sync_at = None
        device.activated_platform = None
        device.app_version = None
        code = self._issue_code(device)
        await self.db.commit()
        await self.db.refresh(device)
        return self._created(device, code)

    # ── read ───────────────────────────────────────────────────────────

    async def get(self, id: UUID, tenant_id: UUID) -> DeviceResponse:
        device = await self.repo.get_by_id(id, tenant_id)
        if not device:
            raise NotFoundError("Device not found.")
        return DeviceResponse.model_validate(device)

    async def list(
        self, tenant_id: UUID, branch_id: UUID | None = None
    ) -> list[DeviceListItem]:
        rows = await self.repo.list_for_tenant(tenant_id, branch_id=branch_id)
        return [
            DeviceListItem(
                **DeviceResponse.model_validate(device).model_dump(),
                branch_name=branch_name,
                branch_code=branch_code,
                sync_status=_sync_status(device.last_sync_at),
            )
            for device, branch_name, branch_code in rows
        ]

    async def limits(self, tenant_id: UUID) -> dict:
        """{used, limit} for the 'N / M devices' hint. limit -1 = unlimited."""
        return {
            "used": await self.repo.count_billable_for_tenant(tenant_id),
            "limit": await self._device_limit(tenant_id),
        }

    # ── lifecycle (tenant) ─────────────────────────────────────────────

    async def _get_or_404(self, id: UUID, tenant_id: UUID) -> Device:
        device = await self.repo.get_by_id(id, tenant_id)
        if not device:
            raise NotFoundError("Device not found.")
        return device

    async def suspend(self, id: UUID, tenant_id: UUID) -> DeviceResponse:
        device = await self._get_or_404(id, tenant_id)
        if device.status == DeviceStatus.REVOKED:
            raise ValidationError("This device has been revoked.")
        device.status = DeviceStatus.SUSPENDED
        if device.suspended_scope != SuspendScope.PLATFORM:
            device.suspended_scope = SuspendScope.TENANT
        await self.db.commit()
        await self.db.refresh(device)
        return DeviceResponse.model_validate(device)

    async def reactivate(self, id: UUID, tenant_id: UUID) -> DeviceResponse:
        device = await self._get_or_404(id, tenant_id)
        if device.status == DeviceStatus.REVOKED:
            raise ValidationError("This device has been revoked and cannot be reactivated.")
        if device.suspended_scope == SuspendScope.PLATFORM:
            raise ValidationError(
                "This device was suspended by the platform. Contact support to restore it."
            )
        if device.status != DeviceStatus.SUSPENDED:
            raise ValidationError("Only a suspended device can be reactivated.")
        device.status = DeviceStatus.ACTIVE
        device.suspended_scope = None
        await self.db.commit()
        await self.db.refresh(device)
        return DeviceResponse.model_validate(device)

    async def revoke(self, id: UUID, tenant_id: UUID) -> DeviceResponse:
        device = await self._get_or_404(id, tenant_id)
        if device.status == DeviceStatus.REVOKED:
            raise ValidationError("Device is already revoked.")
        device.status = DeviceStatus.REVOKED
        device.suspended_scope = None
        device.revoked_at = datetime.now(timezone.utc)
        device.activation_code_hash = None
        device.activation_code = None
        device.activation_code_expires_at = None
        await self.db.commit()
        await self.db.refresh(device)
        return DeviceResponse.model_validate(device)

    async def update(
        self, id: UUID, tenant_id: UUID, data: DeviceUpdate
    ) -> DeviceResponse:
        await self._get_or_404(id, tenant_id)
        device = await self.repo.update(
            id, tenant_id, **data.model_dump(exclude_unset=True)
        )
        await self.db.commit()
        return DeviceResponse.model_validate(device)

    async def delete(self, id: UUID, tenant_id: UUID) -> None:
        if not await self.repo.soft_delete(id, tenant_id):
            raise NotFoundError("Device not found.")
        await self.db.commit()


# ── Shared activation routine (used by the POS activation endpoint) ─────

async def activate_device_with_code(
    db: AsyncSession,
    code: str,
    *,
    platform: str | None = None,
    app_version: str | None = None,
) -> tuple[Device, Branch, Business, Tenant]:
    """Validate a one-time activation code and pair the device.

    Raises ValidationError on any failure. On success the device is ACTIVE and the
    code is consumed.
    """
    from core.exceptions import ValidationError as _VE  # local alias for clarity

    digits = _normalise_code(code)
    if len(digits) != 4:
        raise _VE("Enter the 4-digit activation code.")

    repo = DeviceRepository(db)
    device = await repo.get_by_activation_hash(_hash_code(digits))
    if not device:
        raise _VE("Invalid activation code.")

    now = datetime.now(timezone.utc)
    if device.status == DeviceStatus.SUSPENDED or device.suspended_scope == SuspendScope.PLATFORM:
        raise _VE("This device is suspended.")
    if device.status == DeviceStatus.REVOKED:
        raise _VE("This device has been revoked. Ask your manager to add a new device.")
    if device.activation_code_used_at is not None:
        raise _VE("This activation code has already been used.")
    if device.activation_code_expires_at is None or device.activation_code_expires_at < now:
        raise _VE("This activation code has expired. Generate a new one from the dashboard.")

    row = await db.execute(
        select(Branch, Business, Tenant)
        .join(Business, Branch.business_id == Business.id)
        .join(Tenant, Business.tenant_id == Tenant.id)
        .where(Branch.id == device.branch_id)
    )
    found = row.one_or_none()
    if not found:
        raise _VE("This device's branch no longer exists.")
    branch, business, tenant = found
    if not tenant.is_active or tenant.deleted_at or not branch.is_active or branch.deleted_at or business.deleted_at:
        raise _VE("This business or branch is inactive.")

    device.status = DeviceStatus.ACTIVE
    device.suspended_scope = None
    if device.activated_at is None:
        device.activated_at = now
    device.activation_code_used_at = now
    device.activation_code_hash = None
    device.activation_code = None
    device.activation_code_expires_at = None
    device.last_sync_at = now
    if platform:
        device.activated_platform = platform[:50]
    if app_version:
        device.app_version = app_version[:30]

    await db.commit()
    await db.refresh(device)
    return device, branch, business, tenant
