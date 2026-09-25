# app/main.py
#
# Application entry point.
# Registers global exception handlers and mounts all API routers.
# No business logic belongs here.

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from core.config import settings
from core.exceptions import (
    AuthenticationError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from db.session import engine


class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        if path.endswith((".html", ".js", ".css")):
            response.headers["Cache-Control"] = "no-store"
        return response

from api.v1.pos.router import router as pos_router
from api.v1 import (
    auth,
    tenants,
    business,
    branches,
    categories,
    products,
    variant_option_groups,
    variant_options,
    addon_groups,
    addon_items,
    devices,
    users,
    sales,
    payments,
    refunds,
    dashboard,
    subscription as tenant_subscription,
    roles,
    activity,
    expenses,
    employees,
    attendance,
    salaries,
    tax_rates,
    promotions,
    deals,
    reports,
    inventory_reports,
    preparation_stations,
)
from api.platform import (
    auth as platform_auth,
    dashboard as platform_dashboard,
    tenants as platform_tenants,
    plans as platform_plans,
    subscriptions as platform_subscriptions,
    onboarding as platform_onboarding,
    devices as platform_devices,
    platform_admins,
    activity as platform_activity,
    reports as platform_reports,
    settings as platform_settings,
    employees as platform_employees_hr,
    salaries as platform_salaries,
    business_templates as platform_business_templates,
)


# ================================================================
# LIFESPAN — startup / shutdown
# ================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Nothing to initialise on startup — Alembic handles migrations externally.
    yield
    # Gracefully close all pooled connections so no "too many connections" errors
    # occur when the process restarts (e.g. during hot-reload or k8s rollout).
    await engine.dispose()


# ================================================================
# APPLICATION
# ================================================================

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ================================================================
# CORS
# ================================================================
# Allow the web frontend and any configured origins.
# CORS_ORIGINS="*" in development; set to specific domains in production.

_origins = (
    [o.strip() for o in settings.CORS_ORIGINS.split(",")]
    if settings.CORS_ORIGINS != "*"
    else ["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=_origins != ["*"],  # credentials require explicit origins
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================================================================
# GLOBAL EXCEPTION HANDLERS
# ================================================================
# Registered once here — every route automatically benefits.
# Services raise domain exceptions; this layer converts them to HTTP.

@app.exception_handler(AuthenticationError)
async def authentication_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
    body: dict = {"detail": str(exc)}
    code = getattr(exc, "code", None)
    if code:
        body["code"] = code
    return JSONResponse(status_code=401, content=body)


@app.exception_handler(ForbiddenError)
async def forbidden_handler(request: Request, exc: ForbiddenError) -> JSONResponse:
    body: dict = {"detail": str(exc)}
    code = getattr(exc, "code", None)
    if code:
        body["code"] = code
    return JSONResponse(status_code=403, content=body)


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(ValidationError)
async def validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


# ================================================================
# ROUTERS
# ================================================================

# Tenant API — used by tenant admins and end users.
# `require_module(<key>)` makes an optional module unreachable when the platform
# has disabled it for the tenant (industry templates). Core routers — auth,
# business/settings, dashboard, subscription — are never gated.
API_PREFIX = "/api/v1"
from api.dependencies import require_module  # noqa: E402


def _mod(key: str):
    return [Depends(require_module(key))]


app.include_router(auth.router, prefix=API_PREFIX)
# Tenant administration is exposed only through the platform-authorized API.
app.include_router(business.router, prefix=API_PREFIX)
app.include_router(branches.catalog_router, prefix=API_PREFIX)
app.include_router(branches.router, prefix=API_PREFIX, dependencies=_mod("branches"))
app.include_router(categories.router, prefix=API_PREFIX, dependencies=_mod("menu"))
app.include_router(products.router, prefix=API_PREFIX, dependencies=_mod("menu"))
app.include_router(variant_option_groups.router, prefix=API_PREFIX, dependencies=_mod("menu"))
app.include_router(variant_option_groups.product_router, prefix=API_PREFIX, dependencies=_mod("menu"))
app.include_router(variant_option_groups.category_router, prefix=API_PREFIX, dependencies=_mod("menu"))
app.include_router(variant_options.router, prefix=API_PREFIX, dependencies=_mod("menu"))
app.include_router(addon_groups.router, prefix=API_PREFIX, dependencies=_mod("menu"))
app.include_router(addon_groups.product_router, prefix=API_PREFIX, dependencies=_mod("menu"))
app.include_router(addon_items.router, prefix=API_PREFIX, dependencies=_mod("menu"))
app.include_router(devices.router, prefix=API_PREFIX, dependencies=_mod("devices"))
app.include_router(users.router, prefix=API_PREFIX, dependencies=_mod("users"))
app.include_router(sales.router, prefix=API_PREFIX, dependencies=_mod("sales"))
app.include_router(payments.router, prefix=API_PREFIX, dependencies=_mod("sales"))
app.include_router(refunds.router, prefix=API_PREFIX, dependencies=_mod("sales"))
app.include_router(dashboard.router, prefix=API_PREFIX)
app.include_router(tenant_subscription.router, prefix=API_PREFIX)
app.include_router(roles.router, prefix=API_PREFIX, dependencies=_mod("roles"))
app.include_router(activity.router, prefix=API_PREFIX, dependencies=_mod("activity"))
app.include_router(reports.router, prefix=API_PREFIX, dependencies=_mod("reports"))
from api.v1 import variants
app.include_router(variants.router, prefix=API_PREFIX)
app.include_router(variants.catalog_router, prefix=API_PREFIX)
app.include_router(variants.menu_router, prefix=API_PREFIX)
app.include_router(inventory_reports.router, prefix=API_PREFIX)
app.include_router(expenses.router, prefix=API_PREFIX, dependencies=_mod("expenses"))
app.include_router(employees.router, prefix=API_PREFIX, dependencies=_mod("employees"))
app.include_router(attendance.router, prefix=API_PREFIX, dependencies=_mod("attendance"))
app.include_router(salaries.router, prefix=API_PREFIX, dependencies=_mod("salaries"))
app.include_router(tax_rates.router, prefix=API_PREFIX, dependencies=_mod("menu"))
app.include_router(promotions.router, prefix=API_PREFIX, dependencies=_mod("promotions"))
app.include_router(deals.router, prefix=API_PREFIX, dependencies=_mod("deals"))
app.include_router(preparation_stations.router, prefix=API_PREFIX, dependencies=_mod("kitchen"))

# POS API — used by Android tablets and phones (device + cashier JWT auth)
# Device activation lives at POST /api/v1/pos/auth/activate.
app.include_router(pos_router, prefix=API_PREFIX)

# Platform API — used by the SaaS owner to manage tenants and the platform.
# Every platform router except auth carries `block_readonly_writes`, which 403s a
# `viewer`-tier admin on any POST/PATCH/DELETE (owner/manager pass through).
PLATFORM_PREFIX = "/api/platform"
from api.platform.dependencies import block_readonly_writes  # noqa: E402
_no_readonly = [Depends(block_readonly_writes)]

app.include_router(platform_auth.router, prefix=PLATFORM_PREFIX)
app.include_router(platform_tenants.router, prefix=PLATFORM_PREFIX, dependencies=_no_readonly)
app.include_router(platform_plans.router, prefix=PLATFORM_PREFIX, dependencies=_no_readonly)
app.include_router(platform_subscriptions.router, prefix=PLATFORM_PREFIX, dependencies=_no_readonly)
app.include_router(platform_onboarding.router, prefix=PLATFORM_PREFIX, dependencies=_no_readonly)
app.include_router(platform_devices.router, prefix=PLATFORM_PREFIX, dependencies=_no_readonly)
app.include_router(platform_admins.router, prefix=PLATFORM_PREFIX, dependencies=_no_readonly)
app.include_router(platform_dashboard.router, prefix=PLATFORM_PREFIX, dependencies=_no_readonly)
app.include_router(platform_activity.router, prefix=PLATFORM_PREFIX, dependencies=_no_readonly)
app.include_router(platform_reports.router, prefix=PLATFORM_PREFIX, dependencies=_no_readonly)
app.include_router(platform_settings.router, prefix=PLATFORM_PREFIX, dependencies=_no_readonly)
app.include_router(platform_employees_hr.router, prefix=PLATFORM_PREFIX, dependencies=_no_readonly)
app.include_router(platform_salaries.router, prefix=PLATFORM_PREFIX, dependencies=_no_readonly)
app.include_router(platform_business_templates.router, prefix=PLATFORM_PREFIX, dependencies=_no_readonly)


# ================================================================
# HEALTH CHECK
# ================================================================

@app.get("/health", tags=["Health"])
async def health() -> dict:
    """Simple liveness probe — returns ok if the app is running."""
    return {"status": "ok"}


@app.get("/ready", tags=["Health"])
async def ready():
    from sqlalchemy import text
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        return JSONResponse(status_code=503, content={"status": "unavailable"})


# ================================================================
# UPLOADED MEDIA — product images, etc.
# ================================================================
# Files are written by upload endpoints (e.g. POST /api/v1/products/{id}/image)
# and served read-only from /media/... . Mounted before the catch-all frontend.

_media_root = Path(__file__).parent.parent / "media"
_media_root.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(_media_root)), name="media")


# ================================================================
# STATIC FILES — serve web_fastfood frontend
# ================================================================
# Mounted last so API routes always take priority.
# Resolves the path relative to this file: backend_fastfood/app/../../../web_fastfood

_web_root = Path(__file__).parent.parent.parent / "web_fastfood"
if _web_root.exists():
    app.mount("/", NoCacheStaticFiles(directory=str(_web_root), html=True), name="frontend")
