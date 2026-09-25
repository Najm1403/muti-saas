# api/v1/pos/auth.py
#
# POS authentication endpoints — no standard user auth required.
#
# Flow:
#   1. Tenant admin creates a device and copies the registration_code.
#   2. POS app calls POST /pos/auth/activate with the code → gets a device JWT.
#   3. Cashier calls POST /pos/auth/cashier with username+password → gets a cashier JWT.
#   4. All subsequent POS calls carry the cashier JWT as Bearer token.
#
# Prefix: /api/v1/pos/auth

from __future__ import annotations
from core.auth_limits import limit_auth
from core.security import create_offline_proof

# (datetime import removed - activation moved to device_service)
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import selectinload

from api.dependencies import CurrentDevice, get_user_permissions
from api.v1.pos._guards import operational_device, operational_cashier
from core.exceptions import AuthenticationError, ForbiddenError
from core.security import (
    create_cashier_token,
    create_device_token,
    verify_password,
)
from db.session import get_db
from models.device import Device
from models.user import User
from models.user_branch import UserBranch
from models.user_role import UserRole
from services.cashier_session_service import CashierSessionService
from services.device_service import activate_device_with_code
from schemas.pos_auth import (
    CashierLoginRequest,
    CashierLoginResponse,
    DeviceActivateRequest,
    DeviceActivateResponse,
    StaffMember,
    StaffPinRequest,
)

router = APIRouter(prefix="/auth", tags=["POS — Auth"], dependencies=[Depends(limit_auth)])


async def _assert_can_operate_pos(db: AsyncSession, user_id: UUID, tenant_id: UUID) -> None:
    """Raise unless the user holds pos.operate (or the Admin/Owner/Manager wildcard).

    Both cashier_login and staff_pin_login mint a cashier token — the only way
    to reach a POS session. Without this check, any active, branch-assigned
    user with a password or PIN could operate the register regardless of
    role, which is the wrong default now that PINs are handed out broadly for
    attendance clock-in. See docs/ATTENDANCE.md for the full rationale and how
    to grant pos.operate to a role that needs it.
    """
    perms = await get_user_permissions(db, user_id, tenant_id)
    if "*" not in perms and "pos.operate" not in perms:
        raise ForbiddenError(
            "You don't have permission to operate the POS. Contact your admin.",
            code="POS_ACCESS_DENIED",
        )


async def _assert_no_open_shift_elsewhere(
    db: AsyncSession, user_id: UUID, device_id: UUID, tenant_id: UUID
) -> None:
    """Block signing in on a different device while a shift is already open
    on another one — a cashier may only be "at" one register at a time.
    Signing back into the SAME device that already holds their open shift is
    unaffected (that's just resuming, not a second shift)."""
    other = await CashierSessionService(db).get_open_elsewhere(user_id, device_id, tenant_id)
    if other is not None:
        other_device = await db.get(Device, other.device_id)
        device_label = other_device.name if other_device else "another device"
        raise ForbiddenError(
            f"You already have an open shift on '{device_label}'. "
            "Close it there before signing in here.",
            code="SHIFT_OPEN_ELSEWHERE",
        )


@router.post(
    "/activate",
    response_model=DeviceActivateResponse,
    summary="Activate POS device",
    description=(
        "First-install screen. The POS app submits the one-time 4-digit activation "
        "code the tenant generated in the dashboard (with or without the display space). "
        "Returns a long-lived device JWT plus the business / branch context so the "
        "app needs no follow-up call. The code is consumed on first use."
    ),
)
async def activate_device(
    data: DeviceActivateRequest,
    db: AsyncSession = Depends(get_db),
) -> DeviceActivateResponse:
    device, branch, business, tenant = await activate_device_with_code(
        db,
        data.activation_code,
        platform=data.platform,
        app_version=data.app_version,
    )

    token = create_device_token(
        device_id=device.id,
        branch_id=device.branch_id,
        tenant_id=tenant.id,
    )

    return DeviceActivateResponse(
        device_token=token,
        device_id=device.id,
        device_name=device.name,
        device_type=device.device_type,
        device_letter=device.letter,
        branch_id=branch.id,
        branch_name=branch.name,
        business_id=business.id,
        business_name=business.name,
        tenant_id=tenant.id,
        currency=business.currency,
    )


@router.post(
    "/cashier",
    response_model=CashierLoginResponse,
    summary="Cashier login",
    description=(
        "Called at the start of every shift. The device JWT must be present "
        "in the Authorization header. Returns a cashier JWT valid for 12 hours."
    ),
)
async def cashier_login(
    data: CashierLoginRequest,
    device: CurrentDevice = Depends(operational_device),
    db: AsyncSession = Depends(get_db),
) -> CashierLoginResponse:
    result = await db.execute(
        select(User).where(
            User.username == data.username,
            User.tenant_id == device.tenant_id,
            User.deleted_at.is_(None),
        )
    )
    user = result.scalar_one_or_none()

    # Use the same generic message for both "not found" and "wrong password"
    # so an attacker cannot enumerate valid usernames.
    if not user or not verify_password(data.password, user.password_hash):
        raise AuthenticationError("Invalid username or password.")

    if not user.is_active:
        raise AuthenticationError("User account is deactivated.")

    # GAP 3 — branch assignment check.
    # Unless the user has all_branches=True (e.g. tenant owner / manager),
    # they must be explicitly assigned to this device's branch. Without this
    # check a cashier from Branch A could log in at Branch B and have all
    # their sales attributed to the wrong branch.
    if not user.all_branches:
        branch_check = await db.execute(
            select(UserBranch).where(
                UserBranch.user_id == user.id,
                UserBranch.branch_id == device.branch_id,
            )
        )
        if not branch_check.scalar_one_or_none():
            raise AuthenticationError(
                "You are not assigned to this branch. Contact your manager."
            )

    await _assert_can_operate_pos(db, user.id, device.tenant_id)
    await _assert_no_open_shift_elsewhere(db, user.id, device.device_id, device.tenant_id)

    token = create_cashier_token(
        user_id=user.id,
        device_id=device.device_id,
        branch_id=device.branch_id,
        tenant_id=device.tenant_id,
    )

    return CashierLoginResponse(
        cashier_token=token,
        offline_proof=create_offline_proof(user.id, device.device_id, device.branch_id, device.tenant_id),
        user_id=user.id,
        full_name=user.full_name,
        device_id=device.device_id,
        branch_id=device.branch_id,
        tenant_id=device.tenant_id,
    )


# ── Staff picker + PIN sign-in ───────────────────────────────────────────────
# Used by the tablet's staff-selection screen. Both require the device JWT.


async def _staff_for_branch(db: AsyncSession, device: CurrentDevice) -> list[User]:
    """Active users who may operate this device's branch (all_branches or assigned)."""
    assigned_subq = (
        select(UserBranch.user_id)
        .where(UserBranch.branch_id == device.branch_id)
        .scalar_subquery()
    )
    result = await db.execute(
        select(User)
        .where(
            User.tenant_id == device.tenant_id,
            User.is_active.is_(True),
            User.deleted_at.is_(None),
            (User.all_branches.is_(True)) | (User.id.in_(assigned_subq)),
        )
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
        .order_by(User.full_name)
    )
    return list(result.scalars().unique().all())


def _designation(user: User) -> str:
    for ur in user.user_roles:
        if ur.role is not None:
            return ur.role.name
    return "Staff"


@router.get(
    "/staff",
    response_model=list[StaffMember],
    summary="List staff for this device's branch",
    description=(
        "Returns the active staff shown on the tablet's staff-picker grid — "
        "users with all-branch access or explicitly assigned to this branch. "
        "Requires the device JWT."
    ),
)
async def list_staff(
    device: CurrentDevice = Depends(operational_device),
    db: AsyncSession = Depends(get_db),
) -> list[StaffMember]:
    users = await _staff_for_branch(db, device)
    return [
        StaffMember(
            user_id=u.id,
            full_name=u.full_name,
            designation=_designation(u),
            photo_url=u.photo_url,
            has_pin=u.pin_hash is not None,
        )
        for u in users
    ]


@router.post(
    "/staff-pin",
    response_model=CashierLoginResponse,
    summary="Staff PIN sign-in",
    description=(
        "Called after a staff member is tapped on the grid and enters their PIN. "
        "Verifies pin_hash (falls back to password_hash when no PIN is set) and "
        "returns a cashier JWT. Requires the device JWT."
    ),
)
async def staff_pin_login(
    data: StaffPinRequest,
    device: CurrentDevice = Depends(operational_device),
    db: AsyncSession = Depends(get_db),
) -> CashierLoginResponse:
    result = await db.execute(
        select(User).where(
            User.id == data.user_id,
            User.tenant_id == device.tenant_id,
            User.deleted_at.is_(None),
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise AuthenticationError("Invalid PIN.")
    if not user.is_active:
        raise AuthenticationError("User account is deactivated.")

    pin_ok = (
        verify_password(data.pin, user.pin_hash)
        if user.pin_hash
        else verify_password(data.pin, user.password_hash)
    )
    if not pin_ok:
        raise AuthenticationError("Invalid PIN.")

    if not user.all_branches:
        branch_check = await db.execute(
            select(UserBranch).where(
                UserBranch.user_id == user.id,
                UserBranch.branch_id == device.branch_id,
            )
        )
        if not branch_check.scalar_one_or_none():
            raise AuthenticationError(
                "You are not assigned to this branch. Contact your manager."
            )

    await _assert_can_operate_pos(db, user.id, device.tenant_id)
    await _assert_no_open_shift_elsewhere(db, user.id, device.device_id, device.tenant_id)

    token = create_cashier_token(
        user_id=user.id,
        device_id=device.device_id,
        branch_id=device.branch_id,
        tenant_id=device.tenant_id,
    )
    return CashierLoginResponse(
        cashier_token=token,
        offline_proof=create_offline_proof(user.id, device.device_id, device.branch_id, device.tenant_id),
        user_id=user.id,
        full_name=user.full_name,
        device_id=device.device_id,
        branch_id=device.branch_id,
        tenant_id=device.tenant_id,
    )


@router.get("/payment-permissions")
async def payment_permissions(
    cashier = Depends(operational_cashier),
    db: AsyncSession = Depends(get_db),
):
    from api.dependencies import get_user_permissions
    perms = await get_user_permissions(db, cashier.user_id, cashier.tenant_id)
    can_give_discount = "*" in perms or "sales.discount" in perms
    max_discount_percent = None
    if can_give_discount and "*" not in perms:
        max_discount_percent = await db.scalar(
            select(User.max_discount_percent).where(User.id == cashier.user_id)
        )
    return {
        "can_give_discount": can_give_discount,
        # Null means uncapped — either an admin/owner/manager ("*"), or a
        # cashier with sales.discount but no explicit ceiling set for them.
        "max_discount_percent": str(max_discount_percent) if max_discount_percent is not None else None,
    }
