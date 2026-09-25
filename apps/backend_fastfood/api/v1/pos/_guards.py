# api/v1/pos/_guards.py
#
# Online-only enforcement of device lifecycle. A suspended or revoked device is
# locked out the next time it reaches the server (sync / heartbeat / cashier login).
# Offline devices keep working until they reconnect — matches "internet required".

from __future__ import annotations

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import (
    CurrentCashier,
    CurrentDevice,
    get_current_cashier,
    get_current_device,
)
from core.exceptions import AuthenticationError, ForbiddenError
from models.tenant import Tenant
from models.user import User
from models.user_branch import UserBranch
from db.session import get_db
from models.branch import Branch
from models.device import Device, assert_operational
from models.business import Business


async def _load_device(db: AsyncSession, device_id, branch_id, tenant_id) -> Device:
    result = await db.execute(
        select(Device)
        .join(Branch, Device.branch_id == Branch.id)
        .join(Business, Branch.business_id == Business.id)
        .join(Tenant, Business.tenant_id == Tenant.id)
        .where(
            Device.id == device_id,
            Device.branch_id == branch_id,
            Business.tenant_id == tenant_id,
            Device.deleted_at.is_(None),
            Branch.deleted_at.is_(None), Branch.is_active.is_(True),
            Business.deleted_at.is_(None),
            Tenant.deleted_at.is_(None), Tenant.is_active.is_(True),
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise AuthenticationError("Device not found.", code="DEVICE_NOT_FOUND")
    from models.subscription import Subscription, SubscriptionStatus
    from services.subscription_service import SubscriptionService
    subscription = await db.scalar(select(Subscription).where(Subscription.tenant_id == tenant_id)
        .order_by(Subscription.created_at.desc()).limit(1))
    if subscription:
        # Auto-advances ACTIVE/TRIAL -> PAST_DUE -> SUSPENDED as expires_at +
        # grace_period_days elapse (see SubscriptionService.evaluate_and_sync).
        # PAST_DUE is a deliberate warning-only stage — POS keeps working
        # during it, same as ACTIVE/TRIAL; only SUSPENDED/CANCELLED block.
        subscription = await SubscriptionService(db).evaluate_and_sync(subscription)
        if subscription.status not in {
            SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL, SubscriptionStatus.PAST_DUE,
        }:
            raise ForbiddenError("Subscription is not active. Contact the account owner.", code="SUBSCRIPTION_INACTIVE")
    assert_operational(device)   # raises ForbiddenError w/ code on SUSPENDED / REVOKED
    return device


async def operational_cashier(
    cashier: CurrentCashier = Depends(get_current_cashier),
    db: AsyncSession = Depends(get_db),
) -> CurrentCashier:
    await _load_device(db, cashier.device_id, cashier.branch_id, cashier.tenant_id)
    user = await db.scalar(select(User).where(User.id == cashier.user_id,
        User.tenant_id == cashier.tenant_id, User.deleted_at.is_(None), User.is_active.is_(True)))
    if user is None:
        raise AuthenticationError("Cashier is inactive or unavailable.")
    if not user.all_branches and await db.scalar(select(UserBranch.user_id).where(
        UserBranch.user_id == user.id, UserBranch.branch_id == cashier.branch_id)) is None:
        raise ForbiddenError("Cashier is not assigned to this branch.")
    from api.dependencies import tenant_enabled_modules
    if "sales" not in await tenant_enabled_modules(db, cashier.tenant_id):
        raise ForbiddenError("Sales module is disabled.", code="MODULE_DISABLED")
    return cashier


async def operational_device(
    device: CurrentDevice = Depends(get_current_device),
    db: AsyncSession = Depends(get_db),
) -> CurrentDevice:
    await _load_device(db, device.device_id, device.branch_id, device.tenant_id)
    return device
