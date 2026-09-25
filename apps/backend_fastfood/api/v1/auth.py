from core.auth_limits import limit_auth
# api/v1/auth.py
#
# Authentication routes: login, token refresh, current user, password change.
# No business logic here — all delegated to AuthService.

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentUser, get_current_user
from db.session import get_db
from repositories.user_repository import UserRepository
from schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MeResponse,
    RefreshRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from schemas.common import MessageResponse
from schemas.user import UserResponse
from services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["Authentication"], dependencies=[Depends(limit_auth)])


# ----------------------------------------------------------------
# LOGIN  (public — no token required)
# ----------------------------------------------------------------

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login",
    description=(
        "Authenticate with tenant_code + username + password. "
        "Returns a short-lived access token and a long-lived refresh token."
    ),
)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    return await AuthService(db).login(data)


# ----------------------------------------------------------------
# REFRESH TOKEN  (public — refresh token is the credential)
# ----------------------------------------------------------------

@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh tokens",
    description="Exchange a valid refresh token for a new access + refresh token pair.",
)
async def refresh_token(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    return await AuthService(db).refresh(data)


# ----------------------------------------------------------------
# CURRENT USER  (protected)
# ----------------------------------------------------------------

@router.get(
    "/me",
    response_model=MeResponse,
    status_code=status.HTTP_200_OK,
    summary="Current user",
    description="Return the full profile of the currently authenticated user.",
)
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MeResponse:
    from sqlalchemy import select
    from models.user import User
    from models.tenant import Tenant
    from models.business import Business
    from models.role import Role
    from models.user_role import UserRole

    # Fetch user
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(id=current_user.user_id, tenant_id=current_user.tenant_id)

    # Fetch tenant
    result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id, Tenant.deleted_at.is_(None)))
    tenant = result.scalar_one_or_none()

    # This tenant's shop currency (exactly one business per tenant); default "Rs.".
    currency = await db.scalar(
        select(Business.currency)
        .where(
            Business.tenant_id == current_user.tenant_id,
            Business.deleted_at.is_(None),
        )
        .order_by(Business.created_at)
        .limit(1)
    )

    # Fetch role names for this user
    roles_result = await db.execute(
        select(Role.name)
        .join(UserRole, Role.id == UserRole.role_id)
        .where(
            UserRole.user_id == current_user.user_id,
            UserRole.deleted_at.is_(None),
            Role.deleted_at.is_(None),
            Role.is_active.is_(True),
        )
    )
    role_names = [r for (r,) in roles_result.all()]

    from api.dependencies import get_user_permissions, tenant_enabled_modules
    from services.business_policy import business_feature_flags, load_business_policy
    perms = await get_user_permissions(db, current_user.user_id, current_user.tenant_id)
    modules = await tenant_enabled_modules(db, current_user.tenant_id)
    policy = await load_business_policy(db, current_user.tenant_id)

    # Billing banner — evaluated fresh on every dashboard load/login, not
    # just when a platform admin happens to look at the Subscriptions page,
    # so a lapsed tenant sees this the moment it's true (see
    # SubscriptionService.evaluate_and_sync — there is no scheduled job).
    from datetime import datetime, timedelta, timezone
    from repositories.subscription_repository import SubscriptionRepository
    from schemas.auth import SubscriptionBanner
    from services.subscription_service import SubscriptionService
    subscription_banner = None
    sub = await SubscriptionRepository(db).get_active_for_tenant(current_user.tenant_id)
    if sub:
        sub = await SubscriptionService(db).evaluate_and_sync(sub)
        now = datetime.now(timezone.utc)
        subscription_banner = SubscriptionBanner(
            status=sub.status.value if hasattr(sub.status, "value") else str(sub.status),
            expires_at=sub.expires_at,
            grace_ends_at=sub.expires_at + timedelta(days=sub.grace_period_days),
            days_overdue=(now - sub.expires_at).days if now > sub.expires_at else None,
        )

    from schemas.auth import TenantContext
    return MeResponse(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        email=user.email,
        is_active=user.is_active,
        tenant=TenantContext(
            id=tenant.id if tenant else current_user.tenant_id,
            name=tenant.name if tenant else "Unknown",
            code=tenant.tenant_code if tenant else "",
            is_active=tenant.is_active if tenant else False,
        ),
        currency=currency or "Rs.",
        roles=role_names,
        permissions=sorted(perms),
        modules=sorted(modules),
        business_features=business_feature_flags(policy),
        subscription=subscription_banner,
        admin_message=tenant.admin_message if tenant else None,
        admin_message_set_at=tenant.admin_message_set_at if tenant else None,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


# ----------------------------------------------------------------
# CHANGE PASSWORD  (protected)
# ----------------------------------------------------------------

@router.post(
    "/change-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Change password",
    description="Change the authenticated user's password. Current password must be provided.",
)
async def change_password(
    data: ChangePasswordRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await AuthService(db).change_password(
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
        data=data,
    )
    return MessageResponse(message="Password changed successfully.")


# ----------------------------------------------------------------
# FORGOT PASSWORD  (public — no token required)
# ----------------------------------------------------------------

@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Forgot password",
    description=(
        "Send a 6-digit OTP to the user's registered email address. "
        "Always returns success — never reveals whether the account exists."
    ),
)
async def forgot_password(
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await AuthService(db).forgot_password(data)
    return MessageResponse(message="If the account exists, a reset OTP has been sent.")


# ----------------------------------------------------------------
# RESET PASSWORD  (public — OTP is the credential)
# ----------------------------------------------------------------

@router.post(
    "/reset-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset password",
    description="Complete a password reset using the 6-digit OTP received by email.",
)
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await AuthService(db).reset_password(data)
    return MessageResponse(message="Password reset successfully.")
