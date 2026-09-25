# Execution Flow — login → every screen working

A step-by-step trace of what runs, in which file, for every surface:
**Platform dashboard**, **Tenant dashboard**, and the **POS app** (Android / Windows).

Read a chain left → right:

```
UI file · handler()  →  HTTP METHOD /path  →  router file · route_fn()  [Depends(guard)]
   →  Service.method()  →  Repository / model  →  PostgreSQL
```

`[Depends(...)]` = the FastAPI dependency that must pass first (auth / permission).
All paths below are relative to `apps/`.

---

## 0. Cross-cutting machinery (runs on almost every request)

### 0.1 Token creation & validation — `backend_fastfood/core/security.py`

| Function | Makes / reads | Used by |
|---|---|---|
| `create_access_token(user_id, tenant_id)` | tenant JWT `type=access` (60 min) | tenant login/refresh |
| `create_refresh_token(user_id, tenant_id)` | tenant JWT `type=refresh` (30 d) | tenant login/refresh |
| `create_platform_access_token(admin_id)` | platform JWT `type=platform_access` | platform login/refresh |
| `create_device_token(device_id, branch_id, tenant_id)` | POS JWT `type=device` (30 d) | POS activation |
| `create_cashier_token(user_id, device_id, branch_id, tenant_id)` | POS JWT `type=cashier` | cashier / staff-PIN login |
| `decode_token(token)` | verifies signature + expiry, returns claims | every guard below |
| `hash_password` / `verify_password` | pwdlib bcrypt | login + every password set |

### 0.2 Request guards

**Tenant API** — `backend_fastfood/api/dependencies.py`
- `get_current_user(credentials)` → decodes `access` JWT → `CurrentUser(user_id, tenant_id)`.
- `get_user_permissions(db, user_id, tenant_id)` → `{"*"}` if `User.all_branches` **or** a role named admin/owner/manager, else the concrete `permissions.code` set (join `user_roles → roles → role_permissions → permissions`).
- `require_permission("code")` → dependency factory: runs `get_user_permissions`, raises `ForbiddenError(code="PERMISSION_DENIED")` unless `"*"` or `code` present. Used by **expenses / employees / salaries** routes.
- `get_current_device` / `get_current_cashier` → decode `device` / `cashier` JWT for POS routes.

**Platform API** — `backend_fastfood/api/platform/dependencies.py`
- `get_current_platform_admin(credentials, db)` → decodes `platform_access` JWT, loads the row → `CurrentPlatformAdmin(admin_id, is_super, role)` (role = owner / manager / viewer).
- `require_super(current)` → 403 unless `is_super` (owner tier). Gates Plans, Settings, admin management, destructive HR deletes.
- `block_readonly_writes(request, current)` → **router-level** dependency on every platform router except auth; 403 `ROLE_READ_ONLY` on any POST/PATCH/DELETE when `role == "viewer"`.

**POS operational guards** — `backend_fastfood/api/v1/pos/_guards.py`
- `_load_device(...)` → fetches the `Device`, 401 if gone.
- `operational_device` / `operational_cashier` → wrap the device/cashier guard **and** check `Device.status`; raise `ForbiddenError(code="DEVICE_SUSPENDED" | "DEVICE_REVOKED")` so the app can lock itself.

### 0.3 Domain-exception → HTTP mapping — `backend_fastfood/app/main.py`
`@app.exception_handler(...)`: `AuthenticationError`→401 · `ForbiddenError`→403 (+ optional `code`) · `NotFoundError`→404 · `ConflictError`→409 · `ValidationError`→422.

### 0.4 Front-end plumbing (no build step, plain HTML+JS)

| Surface | Token in `localStorage` | Base | `apiFetch(path, opts)` does |
|---|---|---|---|
| Platform pages | `platform_token` | `const API_BASE = window.API_BASE_URL ?? ''` | `fetch(API_BASE + path, {headers:{Authorization:'Bearer '+token}})`; 401 → wipe token → `/platform/login.html` |
| Tenant pages | `tenant_token` | `const BASE = '/api/v1'` | same shape; 401 → `/tenant/login.html`; `errMsg()` flattens `detail` arrays |
| Shared | — | `/shared/responsive.{css,js}` | off-canvas sidebar < 768 px |

Every dashboard page boots the same way:
`(async () => { const me = await initSidebar(); … })()` where **`initSidebar()`** calls
`GET /auth/me` (tenant) or `GET /api/platform/auth/me` (platform), fills the sidebar/user
box, and returns the profile (incl. `permissions` / `role`). Then the page calls its own
`load*()` functions.

Static files are served by FastAPI itself in dev (`app.mount("/", StaticFiles(..., html=True))`)
and by nginx in production — same relative URLs, no code change.

---

## A. PLATFORM DASHBOARD

Token: `platform_token`. Every call: `Authorization: Bearer <platform_access JWT>`.

### A.1 Login

```
web_fastfood/platform/login.html · form submit
  → POST /api/platform/auth/login   {email, password}
  → backend_fastfood/api/platform/auth.py · login()
      → services/platform_auth_service.py · PlatformAuthService.login(data)
          → repositories/platform_admin_repository.py · get_by_email()
          → core/security.verify_password()
          → core/security.create_platform_access_token(admin.id) + create_platform_refresh_token()
  ← {access_token, refresh_token, ...}
localStorage['platform_token'] = access_token  →  location = '/platform/dashboard.html'
```

**Forgot password** (same page, "Forgot Password?" → reset panel):
```
Step 1  POST /api/platform/auth/forgot-password  {email}
  → api/platform/auth.py · forgot_password()  → PlatformAuthService.forgot_password()
      → PlatformAdminRepository.get_by_email()  → 6-digit OTP  → store SHA-256 hash + 15-min expiry
      → core/email.send_password_reset_otp(admin.email, otp)     (errors logged, never raised; always HTTP 200)
Step 2  POST /api/platform/auth/reset-password  {token, new_password}
  → api/platform/auth.py · reset_password()  → PlatformAuthService.reset_password()
      → PlatformAdminRepository.get_by_reset_token(hash)  → check expiry  → hash_password  → clear token (single-use)
```

### A.2 Dashboard landing — `platform/dashboard.html`

```
initSidebar()  → GET /api/platform/auth/me
   → api/platform/auth.py · get_me()  [Depends(get_current_platform_admin)]
   → PlatformAdminRepository.get_by_id()   ← {id, email, full_name, is_super, role}
loadDashboard()  → GET /api/platform/dashboard
   → api/platform/dashboard.py · get_dashboard()  [Depends(get_current_platform_admin), Depends(block_readonly_writes)]
   → services/onboarding_service.py · OnboardingService.get_dashboard_stats()
       → aggregate queries over tenants / subscriptions / devices / sales
   ← DashboardStats  → KPI cards + charts render
```

### A.3 Module traces (all `[Depends(get_current_platform_admin)]` + router `block_readonly_writes`; writes noted)

| Page | Action → HTTP | Router · fn | Service · method |
|---|---|---|---|
| **tenants.html** | list → `GET /api/platform/tenants/` | `api/platform/tenants.py · list_tenants` | `TenantService.list()` |
| | open → `GET /api/platform/tenants/{id}` | `get_tenant` | `TenantService.get()` |
| | suspend/activate → `POST …/{id}/suspend` \| `/activate` ; delete → `DELETE …/{id}` | `suspend_tenant` / `activate_tenant` / `delete_tenant` | `TenantService.deactivate()` / `activate()` / `delete()` |
| **business-templates.html** | list + presets → `GET /api/platform/business-templates` | `api/platform/business_templates.py · list_templates` | `BusinessTemplateService.list()` |
| | create/edit/delete (**super**) → `POST` \| `PATCH /{id}` \| `DELETE /{id}` `/business-templates` | `create_template` / `update_template` / `delete_template` `[Depends(require_super)]` | `BusinessTemplateService.*` — `config` follows spec Part C's shape (`variants`/`addons`/`inventory`/`pricing`/`product_fields`/`pos`/`categories`/`modules`); "Load Fast Food preset" / "Load Laptop Business preset" buttons fill the JSON editor with a working example; a checkbox grid (synced to `config.modules.hidden`) and the `variants.enabled` checkbox are the two fields also editable outside the raw JSON; 409 if a tenant uses it; save rejects an unknown or mandatory key in `modules.hidden` (`enforce_module_hidden_list`) |
| | tenant usage → `GET /business-templates/{id}/tenants` | `list_template_tenants` | `BusinessTemplateService.tenants_using()` |
| | modules catalog → `GET /business-templates/modules/catalog` | `modules_catalog` | `core/modules.module_catalog()` |
| **create-tenant.html** | plans for the picker → `GET /api/platform/plans` | `api/platform/plans.py · list_plans` | `PlanService.list()` |
| | business templates for the picker (**required** field) → `GET /api/platform/business-templates` | `api/platform/business_templates.py · list_templates` | `BusinessTemplateService.list()` |
| | submit wizard → `POST /api/platform/onboarding/` `{..., business_template_id}` | `api/platform/onboarding.py · onboard` | `OnboardingService.onboard()` → creates Tenant + **Business** (1:1, replaces Restaurant) + Branch + owner User + Subscription, then seeds the template's starting Categories, Variant Option Groups/Options, and Add-on Groups/Items from `business_template.config` |
| **tenant-detail.html** | detail → `GET /api/platform/tenants/{id}` (+ `/onboarding/{id}` enriched) | `onboarding.py · get_tenant_detail` | `OnboardingService.get_tenant_detail()` |
| | users tab → `GET …/{id}/users/` | `tenants.py · list_tenant_users` | `OnboardingService.list_tenant_users()` |
| | **Set password** (write) → `POST …/{id}/users/{uid}/reset-password` (bare JSON string) | `tenants.py · reset_tenant_user_password` | inline: load `User` (tenant-scoped) → `hash_password` → commit |
| | **Account Recovery** (write) → `POST …/{id}/account-recovery` | `tenants.py · account_recovery` | make OTP → store hash+expiry on owner → `PlatformSettingService.get_all()` → `core/email.send_platform_recovery_email()` |
| | branches → `GET/POST …/{id}/branches/`, `PATCH …/{id}/branches/{bid}` | `list_tenant_branches` / `create_tenant_branch` / `update_tenant_branch` | `OnboardingService.*` |
| | devices → `GET …/{id}/devices/` | `list_tenant_devices` | `OnboardingService.list_tenant_devices()` |
| | **Modules tab** (read-only) → `GET …/{id}/detail` for `business_template_id`, then `GET /business-templates/{id}` for its `config.modules.hidden` | `onboarding.py · get_tenant_detail`, `business_templates.py · get_business_template` | Module visibility is decided per Business Template, not per tenant — this tab just resolves and displays it, with a link to edit it on **business-templates.html** |
| **config-reference.html** | Full `config` JSON schema reference + "how to edit" walkthrough — a static reference page, no tenant-specific data | — | — |
| **plans.html** | list → `GET /api/platform/plans?include_inactive=true` | `plans.py · list_plans` | `PlanService.list()` |
| | create/edit/delete (**super only**) → `POST` \| `PATCH /{id}` \| `DELETE /{id}` | `create_plan` / `update_plan` / `delete_plan`  `[Depends(require_super)]` | `PlanService.create/update/delete()` |
| | *(UI)* yearly price auto = 12 × monthly (`recalcYearly()`); the yearly-discount % is applied by `compute_billing`, not baked in |
| **subscriptions.html** | list → `GET /api/platform/subscriptions` | `api/platform/subscriptions.py · list_subscriptions` | `SubscriptionService.list()` |
| | assign plan → `POST /api/platform/subscriptions` | `create_subscription` | `SubscriptionService.create()` |
| | discount override → `PATCH …/{id}` `{discount_pct}` | `update_subscription` | `SubscriptionService.update()` → `compute_billing()` |
| | billing preview → `GET …/{id}/billing-preview` | `billing_preview` | `SubscriptionService.get_billing_preview()` |
| | record payment → `POST …/{id}/payments` | `record_payment` | `SubscriptionService.record_payment()` (amount auto-fills to net price) |
| | payment history → `GET …/{id}/payments` | `list_payments` | `SubscriptionService.list_payments()` |
| **platform_users.html** | list → `GET /api/platform/admins` | `api/platform/platform_admins.py · list_platform_admins` | `PlatformAdminRepository.list()` |
| | create (**super only**) → `POST /api/platform/admins/` `{full_name,email,password,role}` | `create_platform_admin` | `_normalise_role()` → `PlatformAdminRepository.create(role,is_super)` |
| | set role / active (**super**) → `PATCH /{id}` \| `POST /{id}/activate` \| `/deactivate` | `update_platform_admin` / `activate` / `deactivate` | `_normalise_role()` + `PlatformAdminRepository.update()` |
| | Set Password (**super**) → `POST /{id}/reset-password` | `reset_platform_admin_password` | `PlatformAuthService.admin_reset_password()` |
| **employees.html** (Platform HR) | list + analytics → `GET /api/platform/employees`, `GET /api/platform/salaries/summary`, `GET /api/platform/employees/departments`, `GET /api/platform/auth/me` | `api/platform/employees.py` / `salaries.py` | `PlatformHRService.list_employees()` / `.summary()` / `.departments()` |
| | add/edit → `POST` \| `PATCH /{id}` | `create_employee` / `update_employee` | `PlatformHRService.create_employee()` (auto `PLT-0001` via `_next_employee_no()`) / `update_employee()` |
| | archive (**super only**) → `DELETE /{id}` | `delete_employee`  `[Depends(require_super)]` | `PlatformHRService.delete_employee()` |
| **salaries.html** (Platform HR) | month view → `GET /api/platform/salaries/register?month&year` + `/summary` | `salaries.py · payroll_register` / `payroll_summary` | `PlatformHRService.payroll_register()` (each active employee × paid/pending/unpaid) / `.summary()` |
| | record / edit pay → `POST /api/platform/salaries` \| `PATCH /{id}` | `create_payment` / `update_payment` | `PlatformHRService.create_payment()` (net = gross+bonus−deductions; one row per employee×period) / `update_payment()` |
| | delete row (**super only**) → `DELETE /{id}` | `delete_payment`  `[Depends(require_super)]` | `PlatformHRService.delete_payment()` |
| **reports.html** | each panel → `GET /api/platform/reports/{summary\|tenants\|subscriptions\|plans\|branches\|devices\|users\|activity\|revenue}` | `api/platform/reports.py` | `ReportService.get_summary()` / `get_tenant_report()` / `get_subscription_report()` / `get_plan_performance()` / `get_branch_report()` / `get_device_report()` / `get_user_report()` / `get_activity_report()` / `get_revenue_report()` |
| **settings.html** | load → `GET /api/platform/settings` | `api/platform/settings.py · get_settings` | `PlatformSettingService.get_all()` |
| | save section (**super only**) → `PATCH /api/platform/settings` `{key:value}` | `update_settings`  `[Depends(require_super)]` | `PlatformSettingService.update()` — **upserts** allow-listed keys (`smtp_*`, `platform_name`, …); unknown keys ignored |
| | **My Account → Change Password** (any admin, no email) → `POST /api/platform/auth/change-password` `{current_password, new_password}` | `api/platform/auth.py · change_password` | `PlatformAuthService.change_password()` — verifies current, `hash_password`, commit |
| **activity.html** | feed → `GET /api/platform/activity` | `api/platform/activity.py` | `OnboardingService.list_activity()` reads `audit_logs` |
| **sync-health.html** | all devices → `GET /api/platform/devices` | `api/platform/devices.py · list_all_devices` | `OnboardingService.list_all_devices()` |
| | emergency suspend/revoke → `POST /api/platform/devices/{id}/suspend\|reactivate\|revoke` | `platform_device_*` | `services/platform_device_service.py` (sets `suspended_scope=PLATFORM`) |

---

## B. TENANT DASHBOARD

Token: `tenant_token` (`type=access`, carries `tenant_id`). Every service call is scoped to that
`tenant_id` — cross-tenant reads return 404 / empty.

### B.1 Login

```
web_fastfood/tenant/login.html · form submit   {tenant_code, username, password}
  → POST /api/v1/auth/login
  → backend_fastfood/api/v1/auth.py · login()
      → services/auth_service.py · AuthService.login(data)
          → repositories/tenant_repository.py · get_by_code(tenant_code)
          → repositories/user_repository.py · get_by_username(username, tenant.id)
          → core/security.verify_password()
          → create_access_token(user.id, tenant.id) + create_refresh_token(...)
  ← {access_token, refresh_token}
localStorage['tenant_token'] = access_token
  → GET /api/v1/auth/me  (fills localStorage['tenant_me'])  → location = '/tenant/dashboard.html'
```

**Forgot password** (same page, "Forgot password?"):
```
Step 1  POST /api/v1/auth/forgot-password  {tenant_code, email}
  → auth.py · forgot_password()  → AuthService.forgot_password()
      → UserRepository.get_by_email()  → make 6-digit OTP  → store SHA-256 hash + 15-min expiry
      → core/email.send_password_reset_otp(user.email, otp)      (errors logged, never raised; always HTTP 200)
Step 2  POST /api/v1/auth/reset-password  {tenant_code, token, new_password}
  → auth.py · reset_password()  → AuthService.reset_password()
      → UserRepository.get_by_reset_token(hash)  → check expiry  → hash_password  → clear token
```

### B.2 `/auth/me` — powers every sidebar + permission gate

```
GET /api/v1/auth/me   [Depends(get_current_user)]
  → api/v1/auth.py · get_me()
      → api/dependencies.get_user_permissions(db, user_id, tenant_id)
      → api/dependencies.tenant_enabled_modules(db, tenant_id)   → core/modules.effective_modules_from_hidden()
  ← MeResponse {username, full_name, email, roles[], permissions[], modules[], tenant{…}, currency}
```
`permissions` is `["*"]` for Admin/Owner/Manager or `all_branches` users, else the concrete
codes — pages use it to show/hide Add/Edit/Delete controls.
`modules` is the module keys this tenant may use (decided by its Business Template's
`config.modules.hidden` — see B.5); every module when the template hides none. `shared/
responsive.js` reads it to hide disabled sidebar links and swap the page body for a "not
in your plan" notice on a disabled module.

### B.3 Dashboard landing — `tenant/dashboard.html`

```
initSidebar()   → GET /api/v1/auth/me     (as B.2)
loadStats()     → GET /api/v1/dashboard   [Depends(get_current_user)]
   → api/v1/dashboard.py · get_dashboard()
   → services/tenant_dashboard_service.py · TenantDashboardService.get_stats(tenant_id)
       → today/week/month sales, top products, low stock, open shifts
   ← TenantDashboardStats  → KPI cards
```

### B.5 Module gating — which sections a tenant sees

Decided per **Business Template**, not per tenant — `config.modules.hidden` (a list of
module keys, absent/empty = every module visible) on the tenant's Business Template.
Edited from **Platform → Business Templates** (checkbox grid, synced to the JSON); see
`config-reference.html` for the full schema. There is no per-tenant override — every
tenant on the same template sees the same modules.

```
enforcement (backend):
  app/main.py  →  include_router(<optional router>, dependencies=[Depends(require_module("<key>"))])
    require_module(key)  → api/dependencies.tenant_enabled_modules(db, tenant_id)
                         → services/business_policy.load_business_policy(db, tenant_id)
                         → core/modules.effective_modules_from_hidden(config.modules.hidden)
                         → 403 { code: "MODULE_DISABLED" }  when key not in the set
  gated: branches · menu (categories/products/variant-option-groups/variant-options/
         addon-groups/addon-items/tax-rates) · devices · users · sales
         (+payments/refunds) · roles · activity · reports · inventory · expenses · employees
         · salaries · promotions · deals · kitchen (preparation-stations)
  never gated: auth · business/settings · dashboard · subscription · pos/*
  also enforced for POS: api/v1/pos/_guards.py's operational_cashier() (sales module),
  services/offer_service.py (promotions/deals modules) — both call the same
  tenant_enabled_modules(), so a hidden module is respected in the Flutter POS too even
  though the app itself has no client-side notion of modules

nav + page (frontend):
  shared/responsive.js · gateModules()  → GET /api/v1/auth/me  → me.modules
      → hide `aside a[href^="/tenant/"]` links whose page isn't allowed
      → if the current page is a disabled module → replace <main> with a "not in your plan" card
```

### B.4 Module traces (`[Depends(get_current_user)]` unless a permission dep is named)

Every router below is **also** behind `require_module("<key>")` (see B.5) — a tenant whose
plan excludes that module gets 403 `MODULE_DISABLED` and never sees the nav link.

| Page | Action → HTTP | Router · fn | Service · method |
|---|---|---|---|
| **sales.html** | list → `GET /api/v1/sales?branch_id&date_from&date_to&status&user_id&session_id` | `api/v1/sales.py · list_sales` | `SaleService.list(tenant_id, …)`; filters are cumulative and branch-scoped |
| | detail → `GET /api/v1/sales/{id}` | `get_sale` | `SaleService.get()` |
| | detail is read-only in the tenant UI; cashier cancellation and item returns use the guarded POS flows documented in `apps/backend_fastfood/docs/POS_RETURNS_AND_CANCELLATIONS.md` | `api/v1/pos/sales.py` | `PosReturnService.cancel()` / `.return_items()` |
| **reports.html** | panels → `GET /api/v1/reports/{summary\|daily\|products\|cashiers\|branches\|monthly\|yearly\|payment-methods}` with branch/date/cashier/shift scope where supported | `api/v1/reports.py` | `TenantReportService.get_summary()` / `get_daily()` / `get_top_products()` / `get_by_cashier()` / `get_by_branch()` / `get_monthly()` / `get_yearly()` / `get_by_payment_method()` |
| **menu.html** | categories → `GET/POST/PATCH/DELETE /api/v1/categories` | `api/v1/categories.py` | `CategoryService.*` |
| | products → `GET /api/v1/products?category_id`, `POST`, `PATCH /{id}`, `POST /{id}/activate\|deactivate`, `DELETE /{id}` | `api/v1/products.py` | `ProductService.list/create/update/activate/deactivate/delete()` — no `base_price`; Add Product sends the plain/default price/opening stock or `priced_variant_group_id` + one price/opening-stock payload per Color; Cost Price is optional; `sku`/`warranty` are optional and template-gated |
| | product photo → `POST /api/v1/products/{id}/image` (multipart) / `DELETE` | `upload_image` / `delete_image` | Pillow resize → `media/products/<id>.<ext>` |
| | branch availability → `GET/PUT /api/v1/products/{id}/branches` | `get/set_branch_assignment` | `ProductService.get_branch_assignment()` / `set_branch_assignment()` |
| **menu/product-detail.html** | Variant Selections (shared inventory-component choices) → `GET/POST/PATCH/DELETE /api/v1/variant-option-groups`, `/variant-options`; per-product attach → `GET/POST/DELETE /api/v1/products/{id}/variant-option-groups` | `api/v1/variant_option_groups.py`, `variant_options.py` | `VariantOptionGroupService.*`, `VariantOptionService.*` — attaching a selection does not generate product combination Variants |
| | Add-ons — structurally separate section, never feeds variant generation (spec A1/D4) → `GET/POST/PATCH/DELETE /api/v1/addon-groups`, `/addon-items`; per-product attach → `GET/POST/DELETE /api/v1/products/{id}/addon-groups` | `api/v1/addon_groups.py`, `addon_items.py` | `AddonGroupService.*`, `AddonItemService.*` |
| | Existing color Variant prices → `PATCH /api/v1/variants/{id}`; read-only Overall Stock is derived from `GET /api/v1/variants?product_id=...`. Colors are created only in Add Product and are not added/removed here. | `api/v1/variants.py` | `VariantService.update()` / `.stock_snapshot()` |
| | product specs (repeatable key/value, template-gated) → `GET/POST/PATCH/DELETE /api/v1/products/{id}/specs` | `api/v1/products.py` | `ProductService.list_specs/add_spec/update_spec/delete_spec()` |
| **promotions.html** | `GET/POST/PATCH/DELETE /api/v1/promotions` (+ `/evaluate`, `/{id}/branches`) | `api/v1/promotions.py` | `PromotionService.*` |
| **deals.html** | `GET/POST/PATCH/DELETE /api/v1/deals` (+ items, `/{id}/branches`) | `api/v1/deals.py` | `DealService.*` |
| **branches.html** | list + stats → `GET /api/v1/branches/stats` ; CRUD → `GET/POST/PATCH/DELETE /api/v1/branches` | `api/v1/branches.py` | `BranchService.list/create/update/activate/deactivate/delete()` + `BranchStatsService` |
| **preparation-stations.html** | `GET/POST/PATCH/DELETE /api/v1/branches/{id}/preparation-stations` | `api/v1/preparation_stations.py` | `PreparationStationService.*` (server-only config, no offline sync) |
| **devices.html** | list → `GET /api/v1/devices` ; branch picker → `GET /api/v1/branches/stats` — both via `Promise.allSettled`, so a failing `limits`/`branches` call no longer leaves the page stuck on "Loading devices…" (device list is the only hard dependency; on its failure → inline error + **Retry**) | `api/v1/devices.py · list_devices` | `DeviceService.list(tenant_id)` |
| | limits → `GET /api/v1/devices/limits` | `device_limits` | `DeviceService.limits()` (used / plan `max_devices`) |
| | sync-health → `GET /api/v1/devices/sync-health` | `list_device_sync_health` | `DeviceService.list()` + last-sync |
| | **Add Device** → `POST /api/v1/devices` `{name,branch_id,purpose}` | `create_device` | `DeviceService.create()` → 4-digit code, sha256 hash + plaintext, 15-min expiry, `status=PENDING`; 409 if plan cap hit |
| | **Show code** → `GET /api/v1/devices/{id}/activation-code` | `show_activation_code` | `DeviceService.get_code()` — returns the live code, or `{expired:true}` / `{used:true}` so the page shows a popup ("code expired — generate a new one" / "already activated — use Reset") instead of digits |
| | **New code** → `POST /api/v1/devices/{id}/activation-code` | `regenerate_activation_code` | `DeviceService.regenerate_code()` — **409 `ConflictError` if `activated_at` is set** (already paired) |
| | **Reset** → `POST /api/v1/devices/{id}/reset` | `reset_device` | `DeviceService.reset()` — `ACTIVE`/`SUSPENDED` → `PENDING`, clears `activated_at`/session fields, issues a fresh code; old install fails `assert_operational` on next sync; device keeps its plan slot |
| | suspend/reactivate/revoke → `POST /api/v1/devices/{id}/{suspend\|reactivate\|revoke}` | `suspend_device` / `reactivate_device` / `revoke_device` | `DeviceService.suspend/reactivate/revoke()` (`suspended_scope=TENANT`) |
| | edit / delete → `PATCH /{id}` \| `DELETE /{id}` | `update_device` / `delete_device` | `DeviceService.update()` / `delete()` |
| | row status label ← `DeviceListItem.activation_state` (`not_activated` · awaiting code / `code_expired` / `activated` / `suspended` / `revoked`) | — | model computed property |
| **inventory.html** | list → `GET /api/v1/variants?tracked_only=true`; set/increase/decrease → `POST /api/v1/variants/{id}/stock[/{increase\|decrease}]`; transfer → `POST /api/v1/variants/{id}/transfer`; history → `GET /api/v1/variants/{id}/history` | `api/v1/variants.py` | `VariantService.list/set_stock/adjust_stock/transfer_stock/history()` |
| **expenses.html** | gate: `me.permissions` ⊇ `expenses.view` | | |
| | KPIs + monitor → `GET /api/v1/expenses/summary?date_from&date_to` | `api/v1/expenses.py · expense_summary`  `[Depends(require_permission("expenses.view"))]` | `ExpenseService.summary()` (by month/category/branch/method vs budget) |
| | list → `GET /api/v1/expenses?…` ; categories → `GET /api/v1/expenses/categories` | `list_expenses` / `list_categories`  `[expenses.view]` | `ExpenseService.list()` / `list_categories()` |
| | add/edit/delete → `POST`/`PATCH /{id}`/`DELETE /{id}` (+ `/categories`) | `[Depends(require_permission("expenses.manage"))]` | `ExpenseService.create()` (sets `recorded_by`) / `update()` / `delete()` ; `delete_category()` 409 if in use |
| **employees.html** | gate: `employees.view` (helpers in `tenant/hr-common.js`) | | |
| | list + analytics → `GET /api/v1/employees?status&department&branch_id&q`, `GET /api/v1/salaries/summary`, `GET /api/v1/employees/departments`, `GET /api/v1/branches/stats` | `api/v1/employees.py` / `salaries.py`  `[require_permission("employees.view" / "salaries.view")]` | `HRService.list_employees()` / `.summary()` / `.departments()` |
| | add/edit → `POST` \| `PATCH /{id}` | `create_employee` / `update_employee`  `[employees.manage]` | `HRService.create_employee()` — auto `EMP-0001` **per tenant** via `_next_employee_no()`; `_verify_branch()` / `_verify_user()` |
| | archive → `DELETE /{id}` | `delete_employee`  `[employees.manage]` | `HRService.delete_employee()` (keeps salary history; sets `terminated` if paid rows exist) |
| **salaries.html** | gate: `salaries.view` | | |
| | month register → `GET /api/v1/salaries/register?month&year` | `payroll_register`  `[salaries.view]` | `HRService.payroll_register()` — every non-terminated employee × **paid / pending / unpaid** |
| | analytics + trend → `GET /api/v1/salaries/summary` | `payroll_summary`  `[salaries.view]` | `HRService.summary()` — headcount, monthly commitment, coverage %, 6-month `by_month`, `by_department`, `by_status` |
| | record / edit pay → `POST /api/v1/salaries` \| `PATCH /{id}` | `create_payment` / `update_payment`  `[salaries.manage]` | `HRService.create_payment()` — gross defaults to `employee.monthly_salary`; `net = gross+bonus−deductions`; `UniqueConstraint(employee_id, year, month)` → 409 dup; sets `recorded_by` |
| | delete row → `DELETE /{id}` | `delete_payment`  `[salaries.manage]` | `HRService.delete_payment()` (soft) |
| **users.html** | list/CRUD → `GET/POST/PATCH/DELETE /api/v1/users` (+ `/{id}/branches`, `/{id}/roles`). The list is **every** tenant user — dashboard logins **and** POS-only staff (a `User` with a `pin_hash`). | `api/v1/users.py` | `UserService.*` |
| | **Set PIN** (per row) — directly set a staff member's POS PIN → `POST /api/v1/users/{id}/set-pin` | `set_pin` | `UserService.set_pin()` → `pin_hash` |
| | **Reset Pwd** (per row) — force-set any user's password, **no email** → `POST /api/v1/users/{id}/reset-password` (bare JSON string) | `admin_reset_password` | `UserService` → `hash_password` |
| **roles.html** | roles → `GET/POST/PATCH/DELETE /api/v1/roles` | `api/v1/roles.py` | `RoleService.list/create/update/delete()` |
| | permission catalog → `GET /api/v1/roles/permissions/all` | `list_all_permissions` | `RoleService.list_permissions()` (all `permissions` rows incl. `expenses.*`, `employees.*`, `salaries.*`) |
| | role's current perms → `GET /api/v1/roles/{id}/permissions` | `list_role_permissions` | `RoleService.list_role_permissions()` |
| | tick → `POST /api/v1/roles/{id}/permissions` `{permission_id}` ; untick → `DELETE /api/v1/roles/{id}/permissions/{permission_id}` | `assign_permission` / `remove_permission` | `RoleService.assign_permission()` / `remove_permission()` |
| | assign role to user → `POST/DELETE /api/v1/users/{uid}/roles/{rid}` (via `users.py`) | `assign_user_role` / `remove_user_role` | `RoleService.assign_user_role()` / `remove_user_role()` |
| **activity.html** | `GET /api/v1/activity` | `api/v1/activity.py` | `ActivityService` reads `audit_logs` (tenant-scoped) |
| **subscription.html** | plan + price → `GET /api/v1/subscription` | `api/v1/subscription.py · get_subscription` | `TenantSubscriptionService.get_current(tenant_id)` — plan, discount, **net** price; no platform IDs leaked |
| | payment history → `GET /api/v1/subscription/payments` | `list_payments` | `TenantSubscriptionService.list_payments()` |
| **variant-options.html** | business-wide Variant Option Group library (independent of any one product) → `GET/POST/PATCH/DELETE /api/v1/variant-option-groups`, `/variant-options` | `api/v1/variant_option_groups.py`, `variant_options.py` | `VariantOptionGroupService.*`, `VariantOptionService.*` |
| **addon-groups.html** | business-wide Add-on Group library → `GET/POST/PATCH/DELETE /api/v1/addon-groups`, `/addon-items` | `api/v1/addon_groups.py`, `addon_items.py` | `AddonGroupService.*`, `AddonItemService.*` |
| **settings.html** | shop → `GET /api/v1/business` ; save → `PATCH /api/v1/business` | `api/v1/business.py` | `BusinessService.get()` / `update()` (currency, name…) |
| | template config (read-only, for UI field gating) → `GET /api/v1/business/template-config` | `get_template_config` | `load_business_policy()` — real enforcement stays server-side; this is UI gating only |
| | **My Account → Change Password** (own password, no email) → `POST /api/v1/auth/change-password` `{current_password, new_password}` | `api/v1/auth.py · change_password` | `AuthService.change_password()` — verifies current, then `hash_password` |

---

## C. POS APP  (Flutter — Android tablet / phone / Windows desktop)

Entry point `flutter_app_fastfood/lib/main.dart → _Root` watches `syncServiceProvider`
(starts the background sync timer) then builds `FastFoodPosApp` (`lib/app.dart`).

### C.1 The router gate — `lib/app.dart · router()`

`GoRouter.redirect` re-runs on every `onboarding` / `auth` / `session` change and enforces:

```
1. !onboarding.onboarded          → /activate
2. !auth.isCashierLoggedIn        → /staff
3. session == null                → /shift/open
4. otherwise                      → /dashboard   (/pos, /pos/checkout, /pos/receipt/:id reachable)
DEVICE_REVOKED  → onboardingNotifier.resetOnboarding() → /activate
DEVICE_SUSPENDED → DeviceLockedScreen overlay (app.dart builder)
```

Providers behind the gate (`lib/providers/`):
`onboardingNotifierProvider` · `authNotifierProvider` · `sessionNotifierProvider` ·
`deviceLockProvider` (set by the Dio error interceptor).

### C.2 Device activation — `/activate`

```
lib/features/activation/activation_screen.dart · submit(code)
  → providers/onboarding_notifier.dart · OnboardingNotifier.activate(code)
      → providers/repository_providers.dart → features/auth/auth_repository.dart · activateDevice(code, platform, appVersion)
          → core/api/pos_auth_api.dart  → POST /api/v1/pos/auth/activate   {activation_code, platform?, app_version?}
              → backend: api/v1/pos/auth.py · activate_device()
                  → services/device_service.py · activate_device_with_code()
                      → hash code, match PENDING device, check expiry/binding, set status=ACTIVE, activated_at
                      → core/security.create_device_token(device_id, branch_id, tenant_id)
              ← {device_token, device_id, device_name, device_type, branch_id, branch_name,
                 business_id, business_name, tenant_id, currency}
      → core/security/token_storage.dart  saves device_token (flutter_secure_storage)
      → db/daos/settings_dao.dart  persists business_id / business_name / branch_id / currency
  → onboarding state flips onboarded=true  → router redirects to /staff
```

### C.3 Initial catalog sync (runs right after activation and on a timer)

Sync in this codebase is always a **full replace** — `deltaSync()` just calls `fullSync()`,
which wraps `clearCatalog()` + re-apply in one transaction, so removals and option-only edits
propagate correctly without separate delta-diff logic (spec F5).

```
lib/services/sync_service.dart  (timer + connectivity listener)
  → providers/sync_provider.dart → features/sync/sync_repository.dart · fullSync()
      → core/api/pos_sync_api.dart  → GET /api/v1/pos/sync/full   [Depends(operational_cashier)]
          → backend: api/v1/pos/sync.py · sync_full()
              → services/pos_sync_service.py · full_sync(branch_id, tenant_id)
              ← categories, products (plain/default or create-time Color Variant; no base_price;
                inventory-component Variant Selections and Add-ons nested separately),
                **variants** (sale_price/cost_price/stock_by_branch — quantity-only,
                real sellable SKUs, never synthesized client-side),
                tax rates, promotions, deals; inventory_model_version: 6
      → _applyFull(r): writes every row into Drift tables — variants, variant_branch_stock,
        variant_option_groups, variant_options, addon_groups, addon_items,
        plus categories/products/tax/deals/promotions (db/daos/menu_dao.dart, tax_dao.dart)
Later: deltaSync() → fullSync() again (see note above — no separate delta-apply path)
Offline sales flush: uploadOffline(req) → POST /api/v1/pos/sync/upload  (batch)
```

### C.4 Staff sign-in — `/staff`

```
lib/features/staff/staff_screen.dart
  loads roster:  auth_repository.listStaff()
     → GET /api/v1/pos/auth/staff   [Depends(operational_device)]
     → api/v1/pos/auth.py · list_staff()  → _staff_for_branch(db, device)   ← [{user_id, name, designation, has_pin}]
  tap a name → PIN pad (features/staff/widgets/pin_pad.dart)
  submit PIN:
     → providers/auth_notifier.dart · AuthNotifier.staffLoginWithPin(userId, pin)
        → auth_repository.staffLoginWithPin(userId, pin)
           → POST /api/v1/pos/auth/staff-pin   {user_id, pin}   [Depends(operational_device)]
              → api/v1/pos/auth.py · staff_pin_login()
                  → verify pin_hash, then core/security.create_cashier_token(user_id, device_id, branch_id, tenant_id)
           ← {cashier_token}
        → token_storage saves cashier_token → auth.isCashierLoggedIn = true → router → /shift/open
  (Alternative: admin username+password → POST /api/v1/pos/auth/cashier → cashier_login())
```

### C.5 Open shift — `/shift/open`

```
lib/features/shift/shift_open_screen.dart · submit(openingCash)
  → providers/session_notifier.dart · SessionNotifier.openSession(openingCash: …)
      → features/session/session_repository.dart · openSession()
          → core/api/pos_session_api.dart → POST /api/v1/pos/session/open   [Depends(operational_cashier)]
              → api/v1/pos/session.py · open_session()
                  → services/cashier_session_service.py · open(user_id, device_id, branch_id, data)
                      → 422 "A session is already open on this device..." if ANY cashier's shift
                        is still open on this device — the one-open-session-per-device invariant
                        is device-wide, not per-cashier
              ← SessionResponse {id, opened_at, opening_cash}
  → session state set  → router → /dashboard
```

`GET /session/current` (polled by `SessionNotifier.build()` on every app/auth/session change) is
scoped to the CALLING cashier's own `user_id`, not just the device — a session left open by a
different cashier is never silently handed to the next person who logs in on the same device;
they get a 404 (→ router sends them to `/shift/open`, where `open()` above then explains the
device is occupied) instead of inheriting someone else's shift.

### C.6 Dashboard & taking an order

```
lib/features/dashboard/dashboard_screen.dart → tap "New Order" → context.push('/pos')

lib/features/pos/pos_screen.dart  (layout shell)
  ├─ widgets/category_rail.dart   → providers/menu_provider.dart (reads Drift via features/sync/menu_repository.dart)
  ├─ widgets/product_grid.dart    → menu_provider (products for selected category)
  └─ widgets/variant_panel.dart   — three structurally separate concepts (spec F1/F4):
        Product/color SKU → resolves the host product's synced Variant
        Variant Selections → PosNotifier.selectComponent(groupId, optionId), resolves the linked component Variant
        Add-on Groups (checkbox, priced) → PosNotifier.toggleAddon(groupId, itemId, {maxSelections})
        validates each resolved Variant from local quantity stock; no host-product
        combination is synthesized from selected components
        "Add to Cart" → providers/cart_notifier.dart · CartNotifier.addItem(CartItem)
  cart_overlay.dart
        "Park as Draft" → pos_state.dart · DraftNotifier.park(...)
        "Take Payment"  → context.push('/pos/checkout')
```
`CartService` (`features/sale/cart_service.dart`) holds the mutable cart. The product/color
line carries its required `variantId`; each selected component is a linked cart line with
its own Variant and `parentCartItemId`; Add-ons remain priced, `wasRemoved`-aware snapshots.
`CartNotifier`
re-emits a `CartSnapshot` (subtotal / discount / taxAmount / total) on every change.
`features/sale/variant_inventory.dart` backs stock checks with real Drift queries against
`variants`/`variant_branch_stock` — no JSON-blob-in-settings shim.

### C.7 Checkout — `/pos/checkout`

```
lib/features/checkout/checkout_screen.dart
  pick tender (Cash/JazzCash/EasyPaisa/Online Transfer/Credit Card — must match
  core/payment_methods.PAYMENT_METHODS on the backend exactly, 422 otherwise);
  cash → keypad + change = tendered − total
  "Complete Sale":
    cartNotifier.clearPayments(); cartNotifier.addPayment(CartPayment(method, amount, ref))
    online = ref.read(connectivityProvider).valueOrNull
    → providers/repository_providers.dart → features/sale/sale_repository.dart
         · SaleRepository.submitSale(cartSnapshot, isOnline: online)
            id = uuid4();  saleNumber = 'S${year}-${id without dashes}' (globally unique,
              client-generated — not a device-local counter, so two offline devices can
              never collide)
            create = CartSnapshot.toPosSaleCreate(id, saleNumber, sessionId: activeShift.id)
              (cart_service.dart) —
              each item carries the required variantId, a display-only options snapshot,
              and a priced addons list (id/name/price_delta/was_removed)
            if online:
               → core/api/pos_sale_api.dart → POST /api/v1/pos/sales/   [Depends(operational_cashier)]
                   → backend: api/v1/pos/sales.py · create_sale()
                       → services/pos_sale_service.py · create(data, branch_id, device_id, user_id, tenant_id)
                           → resolve_addon_price_deltas(): re-fetches every AddonItem.price_delta from
                             the DB — client-submitted price_delta is never trusted (spec D7)
                           → validates each product/color or component variant_id against its
                             product, re-verifies current sale price, and confirms required
                             Variant Selections are represented by linked component lines
                           → payment-must-cover-total check (no unpaid sale can complete)
                           → writes Sale + SaleItem(+SaleItemOption+SaleItemAddon) + Payment
                             (amount = tendered − returned change; tendered_amount kept separately
                             so change is never counted as revenue)
                           → variant_service.deduct(): per line, row-locked ledger update against
                             VariantBranchStock — no-op unless the variant
                             tracks inventory; raises (→ whole sale rolls back) if it would go
                             negative
               ← PosReceiptResponse
               → cache confirmed receipt in SQLite; prune only synced rows older than
                 90 days                              → SaleResult.online(receipt)
            else / ApiException.isOffline:
               → db/daos/sale_dao.dart · insertSaleWithItems(...)  (offline queue, options +
                 addons persisted per item)
                                                        → SaleResult.queued()
  on result:
    receipt = result.receiptOrNull
    cartNotifier.clear(); posNotifier.resetAll()
    receipt != null → lastReceiptProvider = receipt → context.go('/pos/receipt/<saleId>')
    else            → SnackBar "saved offline" → context.go('/pos')
```

### C.8 Receipt — `/pos/receipt/:id`

```
lib/features/checkout/receipt_screen.dart
  receipt = lastReceiptProvider  (or, on deep-link/relaunch: SaleRepository.getReceipt(id)
            → GET /api/v1/pos/sales/{id}/receipt → pos_sale_service.get_receipt())
  Print → lib/services/pdf_service.dart · printReceipt(receipt)   (pdf + printing packages, 58 mm layout)
  Share → pdf_service.shareReceipt(receipt)
  New Order → lastReceiptProvider = null → context.go('/pos')
```

### C.9 Close shift — `/shift/close`

```
lib/features/shift/shift_close_screen.dart
  live figures → session_notifier.summary()
      → GET /api/v1/pos/session/summary   → cashier_session_service.summary()  (counts, totals, expected cash)
      → SessionSummary.by_payment_method always has all 5 canonical labels (zero-filled),
        legacy free-text values folded onto their label via core/payment_methods.label_lenient
  submit counted cash → session_notifier.closeSession(countedCash: …)
      → POST /api/v1/pos/session/close    → cashier_session_service.close()  ← {session, summary, variance}
        (403 "You can only close your own session..." if this cashier isn't the session owner —
        the device-wide invariant means a stuck device needs its actual owner to close it, or a
        platform/tenant admin to intervene via the web dashboard)
  → "Shift closed" dialog: [Done] logs out → /staff, or [View Details] → /shift-history/:id
    (session state is null either way, but cashierLogout() is deferred until [Done]/leaving that
    screen, so /shift-history/:id stays reachable — see app.dart's redirect exemption below)
```

Tenant dashboard `reports.html` can report across the permitted tenant/branches or narrow every
panel by cashier and shift. `GET /api/v1/reports/payment-methods`
(`tenant_report_service.get_by_payment_method`) omits `group_by` for one overall total over the
selected date range, or uses `day`/`week`/`month`/`year` for one point per period. The POS Reports
screen merges cloud receipts with up to 1,000 recent SQLite rows, deduplicates by sale number,
supports date/cashier/shift filters, and remains readable offline. See
`apps/backend_fastfood/docs/SALES_AND_REPORTING.md` for retention and endpoint limits.

### C.9a Shift history — `/shift-history`, `/shift-history/:id`

The cashier's own "day book" — reviewable any time they're signed in, whether or not a shift is
currently open (`app.dart`'s router exempts `loc.startsWith('/shift-history')` from the
"no open shift → /shift/open" redirect). Reached from the Dashboard's "Shift History" tile, or
directly from the shift-close dialog's "View Details" button.

```
lib/features/shift/shift_history_screen.dart
  → features/session/session_repository.dart · history()
      → GET /api/v1/pos/session/history   [Depends(operational_cashier)]
          → cashier_session_service.py · list_history(user_id, tenant_id)
              ← [SessionResponse] — this cashier's CLOSED shifts, newest first, across every
                device/branch they worked (scoped by user_id only, not device)
  tap a row → /shift-history/:id
    → shift_history_screen.dart · ShiftHistoryDetailScreen
        → session_repository.dart · historySummary(id)
            → GET /api/v1/pos/session/history/{id}/summary   [Depends(operational_cashier)]
                → cashier_session_service.py · history_summary(session_id, user_id, tenant_id)
                    → reuses the same _summary() query summary()/close() use, but by id and
                      without requiring status == OPEN — 404 if the session belongs to someone
                      else or another tenant
                ← SessionSummaryResponse {session, summary}  — same shape as the live close-screen
                  summary, so a shift's full reconciliation stays reviewable after close, not
                  just once at the moment of closing
```

### C.10 Always-on background loops

| Loop | File | Calls |
|---|---|---|
| Full sync + upload + heartbeat | `sync_service.dart · _tick()` | fires on the 5-minute `Timer.periodic`, on app start, and on an offline→online connectivity transition (also on-demand via the Settings "Sync now" button, `retryNow()`) — each tick runs, in order: `_uploadPending()` (batch `POST /api/v1/pos/sync/upload`), `_deltaSync()` (`deltaSync()` just calls `fullSync()` — always a full replace, see C.3), then `_heartbeat()` (`PATCH /api/v1/pos/device/heartbeat` → updates `last_sync_at`; 403 `DEVICE_SUSPENDED`/`REVOKED` → `deviceLockProvider`) |
| Connectivity | `lib/providers/connectivity_provider.dart` | `connectivity_plus` stream → `bool` online, read by checkout + sync |
| Device-lock interceptor | `lib/core/network/dio_client.dart · _ErrorInterceptor` | any 403 with `code` `DEVICE_SUSPENDED`/`DEVICE_REVOKED` → `onDeviceLock(code)` → `DeviceLock` provider → app overlay / reset |

---

## D. File index — surface ↔ router ↔ service

### Backend routers (`backend_fastfood/`)

| Prefix | File | Guard baseline | Service(s) |
|---|---|---|---|
| `/api/v1/auth` | `api/v1/auth.py` | public / `get_current_user` | `AuthService` |
| `/api/v1/dashboard` | `api/v1/dashboard.py` | `get_current_user` | `TenantDashboardService` |
| `/api/v1/business` `/branches` `/categories` `/products` `/variant-option-groups` `/variant-options` `/addon-groups` `/addon-items` `/variants` | resp. files in `api/v1/` | `get_current_user` | `BusinessService` · `BranchService`/`BranchStatsService` · `CategoryService` · `ProductService` · `VariantOptionGroupService` · `VariantOptionService` · `AddonGroupService` · `AddonItemService` · `VariantService` |
| `/api/v1/sales` `/payments` `/refunds` | `api/v1/{sales,payments,refunds}.py` | `get_current_user` | `SaleService` · `PaymentService` · `RefundService` |
| `/api/v1/devices` | `api/v1/devices.py` | `get_current_user` | `DeviceService` |
| `/api/v1/users` `/roles` | `api/v1/{users,roles}.py` | `get_current_user` | `UserService` · `RoleService` |
| `/api/v1/variants` + Variant stock routes; `/tax-rates` `/promotions` `/deals` `/preparation-stations` | `api/v1/…` | `get_current_user` / inventory permissions | `VariantService` · `TaxRateService` · `PromotionService` · `DealService` · `PreparationStationService` |
| `/api/v1/expenses` | `api/v1/expenses.py` | `require_permission("expenses.*")` | `ExpenseService` |
| `/api/v1/employees` `/salaries` | `api/v1/{employees,salaries}.py` | `require_permission("employees.*" / "salaries.*")` | `HRService` |
| `/api/v1/reports` `/activity` `/subscription` | `api/v1/…` | `get_current_user` | `TenantReportService` · `ActivityService` · `TenantSubscriptionService` |
| `/api/v1/pos/**` | `api/v1/pos/{auth,sync,sales,session,device}.py` | `operational_device` / `operational_cashier` | `DeviceService` · `PosSyncService` · `PosSaleService` · `CashierSessionService` |
| `/api/platform/auth` | `api/platform/auth.py` | public / `get_current_platform_admin` | `PlatformAuthService` |
| `/api/platform/tenants` `/onboarding` | `api/platform/{tenants,onboarding}.py` | `get_current_platform_admin` + `block_readonly_writes` | `TenantService` · `OnboardingService` |
| `/api/platform/business-templates` | `api/platform/business_templates.py` | `get_current_platform_admin` + `require_super` on writes | `BusinessTemplateService` |
| `/api/platform/plans` `/settings` | `api/platform/{plans,settings}.py` | + `require_super` on writes | `PlanService` · `PlatformSettingService` |
| `/api/platform/subscriptions` | `api/platform/subscriptions.py` | `+ block_readonly_writes` | `SubscriptionService` (`compute_billing`) |
| `/api/platform/admins` | `api/platform/platform_admins.py` | `_require_super` on writes | `PlatformAdminRepository` · `PlatformAuthService` |
| `/api/platform/employees` `/salaries` | `api/platform/{employees,salaries}.py` | `+ require_super` on delete | `PlatformHRService` |
| `/api/platform/dashboard` `/reports` `/activity` `/devices` | `api/platform/…` | `get_current_platform_admin` | `OnboardingService` · `ReportService` · `platform_device_service` |

### Web pages (`web_fastfood/`)

`platform/`: login · dashboard · tenants · create-tenant · tenant-detail · **business-templates** ·
plans · subscriptions · platform_users · **employees** · **salaries** · reports · settings · activity ·
sync-health · `hr-common.js`
`tenant/`: login · dashboard · sales · reports · menu (+ `menu/product-detail`) · **variant-options** ·
**addon-groups** · promotions · deals · branches · preparation-stations · devices · inventory ·
expenses · **employees** · **salaries** · users · roles · activity · subscription · settings ·
`hr-common.js`
`shared/`: `responsive.css` · `responsive.js` · `safe-text.js` (`escapeHTML`/`escapeJSAttribute`)

### POS app (`flutter_app_fastfood/lib/`)

`main.dart` → `app.dart` (router) →
`features/{activation,staff,shift,dashboard,pos,checkout,settings}/` (screens) ·
`providers/*` (Riverpod notifiers) ·
`features/{auth,sale,session,sync}/` (repositories) ·
`core/api/pos_*_api.dart` (HTTP) · `core/network/dio_client.dart` (token + lock interceptors) ·
`db/` (Drift offline DB) · `services/{sync_service,pdf_service}.dart`.
