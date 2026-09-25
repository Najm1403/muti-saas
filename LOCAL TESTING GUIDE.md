# Local Testing Guide — Multi-SaaS FastFood Platform

End-to-end manual test procedure for a single Windows workstation with PostgreSQL,
one Android **tablet** (emulator or physical), optionally a **phone**, and — new — the
same POS app on **Windows desktop** (`flutter run -d windows`).


You will exercise all three surfaces:
PS D:\muti-saas> cd .\apps\backend_fastfood\
PS D:\muti-saas\apps\backend_fastfood> 
then run a file  python run.py
OR go directly to url for plateform superadmin
http://localhost:8000/platform/login.html

| Surface | What it is | URL / entry point |
|---|---|---|
| **Platform dashboard** | SaaS owner — creates shops, plans, sees every tenant | `http://localhost:8000/platform/login.html` |
| **Shop dashboard** | Shop (restaurant) owner/admin — menu, branches, staff, settings | `http://localhost:8000/tenant/login.html` |
| **POS app** | Android tablet / Windows desktop — device activation, shifts, order taking | Flutter app, points at `http://<host>:8000` |

> **Terminology:** the web UI says **"Shop" / "Shop ID"**; internally the backend calls it
> `business` / `tenant_code` — every tenant owns exactly one `Business` (the old `Restaurant`
> model was removed; see `COMPLETE-IMPLEMENTATION-SPEC.md` Part A/B). The POS no longer asks
> for a Shop ID — the tenant admin creates the device in the Shop dashboard and the POS is
> activated with a **4-digit code**.
>
> **Business Templates:** every shop is created against a platform-managed **Business
> Template** (e.g. "Fast Food", "Electronics Wholesale") chosen at onboarding. The template's
> `config` drives which product fields show (`sku`, `specs`, `warranty`), whether cost price
> and inventory tracking are required or optional, and seeds the shop's starting categories,
> shared **Variant Selections** (e.g. RAM or Storage — reusable inventory components) and
> **Add-on Groups** (e.g. Toppings or Extended Warranty — priced, never affect product
> stock). Product Colors are chosen only in Add Product and create priced/stocked SKUs.
> See Part C4 below.

> **Going to production?** Once local testing passes, follow
> [`deploy/DEPLOYMENT-RUNBOOK.md`](deploy/DEPLOYMENT-RUNBOOK.md). It is the single ordered
> procedure for readiness, VPS provisioning, production configuration, client builds,
> verification, backup, and rollback.
>
> Sales history, date/cashier/shift filtering, POS SQLite retention, and the focused
> verification commands are in
> [`apps/backend_fastfood/docs/SALES_AND_REPORTING.md`](apps/backend_fastfood/docs/SALES_AND_REPORTING.md).

---

## Who does what

This guide has two audiences:

| Role | Does | Sections |
|---|---|---|
| **Developer** (once) | Installs and starts the system: database, server, tablet app | Parts **0, A, D1–D3, E1–E3** |
| **Tester** (anyone, repeatable) | Clicks/taps through the product to check it works | **Tester's Walkthrough** below, then Parts **B, C, D4, E4** for detail |
| **Releaser** (when handing out a real install, or going live) | Builds the `.exe`/installer/APK, then deploys to a real server | Part **H**, then `deploy/DEPLOYMENT-RUNBOOK.md` |

If you are **not** a coder: skip to **"Tester's Walkthrough"**. Ask whoever set up the system
to hand you the five things listed there.

---

## Tester's Walkthrough (no commands, no coding)

Before you start, get these from the person who installed the system:

| # | You need | Example |
|---|---|---|
| 1 | The **web address** of the dashboards | `http://localhost:8000` (or a `192.168.x.x` address) |
| 2 | The **platform login** (the SaaS owner account) | `najamphysics@gmail.com` / `123456` |
| 3 | Confirmation the **tablet app is installed** and pointed at the same address | — |
| 4 | Nothing else — you will create the shop, staff and PIN yourself in steps below | — |

### Step 1 — Create a shop (platform dashboard)

1. In a browser open **`<web address>/platform/login.html`**.
2. Log in with the **platform login** (#2 above).
3. Click **Create Tenant** (or **Tenants → New**). Fill in:
   - Shop name: `Demo Diner`
   - Tenant Code: `DEMO01`  ← *remember this — it is the **Shop ID***
   - **Business Template**: pick `Fast Food` (required — drives which product fields and
     shared Variant/Add-on libraries this shop starts with; see the terminology note above)
   - Currency: `Rs.`
   - Owner name / username / email: `Owner One` / `owner1` / `o1@demo.test`
   - Branch name / code: `Central` / `CEN`
4. Submit. The next screen shows a **temporary password** for `owner1`. **Copy it and keep it.**
5. **✓ You should see** `Demo Diner` in the Tenants list.

### Step 2 — Set up the shop (shop dashboard)

1. Open **`<web address>/tenant/login.html`**.
2. Log in with: Shop Code `DEMO01`, Username `owner1`, Password = the temporary password from Step 1.
   (If it asks you to set a new password, do so and log in again.)
3. **Settings**: check the **Shop ID** box (it says `DEMO01`), set **Currency** to `Rs.`,
   click **Save Shop**.
4. **Branches**: click **Add Branch**, name `Airport`, code `AIR`, save.
   **✓ You should see** two branches: Central and Airport.
5. **Menu** (optional but recommended so the tablet has items to sell):
   add a category `Burgers`, then a product `Cheeseburger` priced `6.50`.
   Under **Settings → Tax Rates** add one rate `GST` = `0.08` and mark it **default**.
6. **Users → Add User**:
   - Full name `Cash One`, username `cash1`, password `cashpass1`
   - **POS PIN**: `2468`
   - Save. On the new row, click **Edit** and set the branch to **Central**.
   **✓ You should see** a green **"PIN set"** badge next to `Cash One`.
7. **Devices → Add Device**: name `Counter POS 1`, branch **Central**, purpose **POS** → **Create Device**.
   A dialog shows a **4-digit activation code** (e.g. `58 32`) with a 15-minute countdown.
   **Keep this screen open** — you'll type the code on the POS next.

### Step 3 — Use the POS (tablet or Windows)

Hold a tablet **sideways (landscape)**; on Windows just resize the window.

1. **Activation screen** — type the **4-digit code** from Step 2.7, tap **Activate**.
   Wrong/expired/used code → an inline error. Success → straight to the Staff screen
   (the shop + branch are already known from the code).
2. **Staff screen** — tap **Cash One**. On the keypad type **`2468`** (or type it on a
   physical keyboard), tap **Sign in**.
3. **Open shift** — type the cash currently in the drawer, e.g. `200.00`, tap **Open shift**.
4. **Dashboard** — you see a greeting and a green "shift open" strip. Tap **New Order**.
5. **Order screen** — tap a category, tap a product. If it has a **Variant** (e.g. Size),
   pick exactly one per group (radio) — this resolves the exact SKU sold, never guessed
   client-side. If it has **Add-ons** (e.g. Extras), tick as many as allowed (checkbox,
   priced) — a pre-checked "default" add-on can be unticked to remove it from the line.
   For a colored product, pick the color SKU and confirm its quantity is available at the
   device branch. Tap **Add to Cart**, then **View Cart → Take payment**. Pick a
   tender — **Cash, JazzCash, EasyPaisa, Online Transfer, or Credit Card** (Cash shows a
   keypad + change due; the other four charge the full amount and take an optional
   reference number) — then **Complete Sale**. Prices show as `Rs. …`.
6. Go back to the **Dashboard**, tap **Close shift** — type the counted cash, e.g. `195.00`.
   You see a summary (opening cash, sales, expected cash, and whether the drawer is over/short).
   Confirm — you return to the Staff screen.
7. Tap the **gear icon** anywhere on the Dashboard to see **Settings**: shop / branch / device
   info, sync status, **Sync now**, and **Deactivate this device** (which sends the POS back to
   the activation screen).
8. **(Optional) Suspend test** — in the Shop dashboard **Devices** page, click **Suspend** on
   `Counter POS 1`. On the POS, the next sync / staff login shows a "device suspended" lock
   screen. Click **Reactivate** in the dashboard → the POS recovers.

**Restart check:** fully close the app and open it again — it should skip straight to the
**Staff screen** (the shop + branch are stored locally).

That is the whole product. The sections below are the technical detail behind each step.

---

## 0. Prerequisites

| Tool | Version | Check |
|---|---|---|
| PostgreSQL | 14+ running on `localhost:5432` | `psql -U postgres -c "select version();"` |
| Python | 3.11.x | `python --version` |
| Flutter SDK | 3.44.x (stable) | `flutter --version` |
| Android Studio | latest, with an SDK + an AVD | `flutter doctor` |
| Java JDK | 17 (bundled with Android Studio) | — |
| A modern browser | Chrome / Edge | — |

Paths used below (adjust if yours differ):

```
Repo root      D:\muti-saas
Backend        D:\muti-saas\apps\backend_fastfood
venv Python    D:\muti-saas\apps\backend_fastfood\.venv\Scripts\python.exe
Flutter app    D:\muti-saas\apps\flutter_app_fastfood
Web dashboards D:\muti-saas\apps\web_fastfood   (served by the backend at /)
```

All backend commands below are **PowerShell**, run from `D:\muti-saas\apps\backend_fastfood`,
and call the venv Python by full path so you never need to activate the venv. If you prefer to
activate it:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass   # this terminal only
.\.venv\Scripts\Activate.ps1                                  # prompt shows (.venv)
```

---

## Part A — Backend + database

### A1. Create a fresh test database

```powershell
psql -U postgres -c "CREATE DATABASE fastfood_test OWNER account_admin;"
```

If the `account_admin` role does not exist:

```powershell
psql -U postgres -c "CREATE ROLE account_admin LOGIN PASSWORD 'admin123' CREATEDB;"
psql -U postgres -c "CREATE DATABASE fastfood_test OWNER account_admin;"
```

### A2. Point `.env` at it

Edit `D:\muti-saas\apps\backend_fastfood\.env`:

```ini
DATABASE_URL=postgresql+psycopg://account_admin:admin123@localhost:5432/fastfood_test
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=<keep the existing value>
CORS_ORIGINS=*
PLATFORM_ADMIN_EMAIL=najamphysics@gmail.com
PLATFORM_ADMIN_PASSWORD=123456
PLATFORM_ADMIN_NAME=Super Admin
```

> Key names must match `core/config.py` — it's `ENVIRONMENT` (not `APP_ENV`) and
> `CORS_ORIGINS` (comma-separated string or `*`). Unknown keys are ignored.

### A3. Install backend dependencies (first run only)

```powershell
cd D:\muti-saas\apps\backend_fastfood
python -m venv .venv                       # only if .venv does not exist
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### A4. Run migrations

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current
```

**✓ Checkpoint:** last line prints `2757039146da (head)`. There is exactly one
migration, `2757039146da_initial_schema`: the full current schema, created
fresh from an empty database and seeded with the permissions catalog and
default Business Templates. `Business` replaces `Restaurant`; `Tenant`
carries a required `business_template_id`; `Product` has no `base_price` —
every product always owns a default `Variant`; `VariantOptionGroup`/
`VariantOption` are shared per-Business and single-select only; `AddonGroup`/
`AddonItem` are the separate multi-select, priced concept; `VariantBranchStock`
backs quantity-only per-branch inventory; `CashierSession.shift_number` (a
`YYMMDD` + device-letter + daily-sequence code) and `CategoryVariantOptionGroup`
are part of the schema from the start; plus every table from the
pre-refactor schema — HR/payroll, device activation codes, `auth_rate_limits`
— carried forward. See `COMPLETE-IMPLEMENTATION-SPEC.md` Parts A–J for the
full model, and `apps/backend_fastfood/docs/SALES_AND_REPORTING.md` for the
reporting features (refunds/cancellations, year comparison, shift cash
reconciliation) added on top of it.
(This is the **second** squash: the 18-migration pre-refactor chain was
folded into `0eb716adc2b6_initial_schema` during the Business/Variant/Add-on
refactor, and that chain — plus every migration added since, including this
one's own predecessor `f2abd477c3dd` — was itself folded into today's single
`2757039146da_initial_schema` ahead of first production deployment. A
database migrated under either older baseline cannot upgrade in place onto
this one and must be recreated.)

### A5. Bootstrap the platform super admin

```powershell
.\.venv\Scripts\python.exe scripts\bootstrap_platform.py
```

**✓ Checkpoint:** prints `Platform super admin created successfully` with
`Email: najamphysics@gmail.com`. (Password is `123456` from `.env`.)

### A6. Start the API server

```powershell
.\.venv\Scripts\python.exe run.py
```

Leave this terminal running. It serves the API **and** the web dashboards. `run.py`
prints the URLs to open — use **`http://localhost:8000`** (or the `192.168.x.x` line
for the tablet). It binds `0.0.0.0` so LAN devices can reach it; `http://0.0.0.0:8000`
itself is a bind address, **not** a browser URL. Bind localhost only with
`.\.venv\Scripts\python.exe run.py --host 127.0.0.1`.
Production values and file ownership are documented in
[`deploy/DEPLOYMENT-RUNBOOK.md`](deploy/DEPLOYMENT-RUNBOOK.md).

### A7. Smoke test

Open a second terminal:

```powershell
curl.exe http://localhost:8000/health
# {"status":"ok"}

curl.exe -s -o NUL -w "%{http_code}`n" http://localhost:8000/platform/login.html   # 200
curl.exe -s -o NUL -w "%{http_code}`n" http://localhost:8000/tenant/login.html     # 200
```

Interactive API docs: `http://localhost:8000/docs`

### A8. (Optional) Run the automated suite

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

**Checkpoint:** the complete suite must pass (the latest verified run was `572 passed`). It
includes the full Business/Variant/Add-on model suite
(`test_menu_services.py`, `test_spec_matrix.py` — spec Part I's dedicated matrix —
`test_cashier_session.py` — shift open/close/current/history, including the cross-cashier
handoff fix — plus `test_subscription_billing.py`, `test_device_lifecycle.py`,
`test_expenses.py`, `test_hr.py`, `test_platform_hr.py`, `test_platform_rbac.py`,
`test_password_flows.py`, `test_module_templates.py`, `test_payment_methods.py`,
`test_inventory_service.py` and the PostgreSQL sales/reporting regressions). Do not treat
the recorded count as permanent; added tests legitimately increase it.
A separate, explicitly-invoked audit probe suite also exists at
`tests/audit_deployment_checks.py` — see `AUDIT_HISTORY.md` for what it checks and how
to run it; it is not part of this count.

---

## URL configuration reference — which file, which value

The FastAPI server **serves the web dashboards itself**, so the web pages need no edits.
Only the Flutter app takes an API URL.

### Flutter POS app

One variable, in **`apps/flutter_app_fastfood/lib/core/network/dio_client.dart`**:

```dart
const _apiUrl = String.fromEnvironment('API_URL', defaultValue: 'http://10.0.2.2:8000');
```

Override it at launch — **do not edit the file** for normal use:

| Target | `API_URL` value | Extra step |
|---|---|---|
| Android emulator | `http://10.0.2.2:8000` | — (`10.0.2.2` = host loopback) |
| Genymotion emulator | `http://10.0.3.2:8000` | — |
| Physical device, USB | `http://localhost:8000` | `adb reverse tcp:8000 tcp:8000` |
| Physical device, Wi-Fi | `http://<PC-LAN-IP>:8000` e.g. `http://192.168.1.20:8000` | same network + firewall rule (§E2) |

```powershell
flutter run -d <device-id> --dart-define=API_URL=http://10.0.2.2:8000
flutter build apk --debug --dart-define=API_URL=http://192.168.1.20:8000
```

HTTP endpoints are for debug/local testing only. Release builds require an explicit
`https://` API URL and the Android release signing configuration.

Make it permanent (pick one):

- **Edit the default:** change `defaultValue` in `dio_client.dart`.
- **JSON file:** create `apps/flutter_app_fastfood/env.json` → `{ "API_URL": "http://192.168.1.20:8000" }`,
  run with `--dart-define-from-file=env.json`.
- **IDE:** VS Code `.vscode/launch.json` → `"args": ["--dart-define=API_URL=http://10.0.2.2:8000"]`;
  Android Studio → edit Run config → *Additional run args*.

### Web dashboards (usually no change)

| Pages | Base URL in code | Where |
|---|---|---|
| `tenant/*.html` (settings, users, branches, dashboard, menu, roles, devices, activity, subscription, preparation-stations, menu/product-detail) | `const BASE = '/api/v1';` (relative) | one line near the top of each file |
| `platform/*.html` (login, dashboard, create-tenant, plans, tenants, tenant-detail, platform_users) | `const API_BASE = window.API_BASE_URL ?? '';` (relative, overridable) | one line near the top of each file |

Open them **through the backend origin** and the relative URLs just work:

```
http://localhost:8000/platform/login.html
http://localhost:8000/tenant/login.html
```

Only if you serve the HTML from a **different** origin (e.g. VS Code Live Server `:5500`):

- **Platform pages:** add `<script>window.API_BASE_URL = 'http://localhost:8000';</script>`
  before the page script, and set `CORS_ORIGINS` in `core/config.py` / `.env`.
- **Tenant pages:** change `const BASE = '/api/v1';` → `const BASE = 'http://localhost:8000/api/v1';`
  in each tenant HTML file (no `window` override exists for these), and set CORS.

### Backend host / port

`apps/backend_fastfood/run.py` — defaults `--host 0.0.0.0 --port 8000`. Override on the CLI
(`python run.py --port 9000`) or change the `default=` values. `0.0.0.0` already means
"reachable from other devices on the LAN".

---

## Part B — Platform dashboard (SaaS owner)

Open `http://localhost:8000/platform/login.html`.

> **Mobile check (any dashboard page):** every `platform/*` and `tenant/*` page now loads
> `shared/responsive.css` + `responsive.js`. In Chrome DevTools device mode at ~390 px the
> sidebar collapses behind a ☰ top-bar button, tables scroll sideways, and drawers go
> full-width. At ≥ 768 px the layout is unchanged.

### B1. Log in

| Field | Value |
|---|---|
| Email | `najamphysics@gmail.com` |
| Password | `123456` |

**✓** You land on the platform dashboard with KPI tiles (tenants, users, branches, devices).

### B2. (Optional) Create a subscription plan

**Plans → New Plan** — set limits (e.g. Shops `1`, Branches `5`, Users `20`, **Devices `2`**),
monthly / yearly price, and optionally **monthly / yearly discount %**. The plan's `max_devices`
is now **enforced** when a tenant adds a device (a tenant with **no plan** may create **1**).
Not required for testing; you can create a shop with no plan.

To exercise discounts: **Subscriptions** → assign this plan to the tenant, set a **per-tenant
discount %**, then **Record Payment** — the amount pre-fills to the discounted (net) price.
The tenant sees it under **Subscription** in their own dashboard.

### B3. Create a shop (tenant onboarding)

**Create Tenant** (or **Tenants → New**). Fill:

| Field | Example |
|---|---|
| Business / Shop name | `Demo Diner` |
| Tenant Code | `DEMO01` |
| Country / Timezone | any |
| **Currency** | `Rs.` (or `$`, `€` …) |
| Owner Full Name | `Owner One` |
| Owner Username | `owner1` |
| Owner Email | `o1@demo.test` |
| Plan | leave empty, or pick one from B2 |
| Branch Name | `Central` |
| Branch Code | `CEN` |

Submit. The confirmation screen shows a **one-time owner temporary password** — **copy it now**
(e.g. `cl0U32jJZxZno7qKD5NnAw`). You cannot see it again.

**✓ Checkpoint:** the new shop appears under **Tenants**. Note its **Tenant Code** (`DEMO01`) —
that is the login code and, as the **Shop ID**, what the tablet needs.

### B4. Verify

**Tenants → Demo Diner** — you should see the owner, 1 branch, 0 devices, and the plan/trial
status. The **Devices** section on this page lists nothing yet; once the tenant adds devices
you can **Suspend / Reactivate / Revoke** them here as a platform override.

---

## Part C — Shop dashboard (shop owner / admin)

Open `http://localhost:8000/tenant/login.html`.

### C1. Log in as the shop owner

| Field | Value |
|---|---|
| Shop / Tenant Code | `DEMO01` |
| Username | `owner1` |
| Password | the temp password from **B3** |

(If prompted to change the password, set a new one and log in again.)

### C2. Shop settings — currency

**Settings** → *Shop Information*:

- **Shop ID** is still shown read-only with a **Copy** button (used for the tenant web login;
  the POS no longer needs it).
- Set **Currency** to `Rs.` (or your choice) and **Save Shop**.

**✓ Checkpoint:** reload the page — the currency you saved is still shown.

### C3. Add a second branch

**Branches → Add Branch**: name `Airport`, code `AIR`. Save.

**✓ Checkpoint:** both `Central` and `Airport` are listed.

### C4. Build a menu (needed to take real orders on the POS)

**Menu**:

1. Add **categories** — e.g. `Burgers`, `Drinks`.
2. Add one plain product and one colored product. A plain product has one **Sale Price** and
   opening stock. For the colored product, choose Colors in **Add Product** and enter each
   color's Sale Price and opening stock; saving creates one real Variant per color.
   If the shop's Business Template marks fields like **SKU**, **specs**, or **warranty** as
   applicable (e.g. an Electronics template), they show here too — always optional. Cost
   Price is also optional.
3. Open each product's detail page:
   - Confirm color membership stays as configured in Add Product and the Sale Price for
     each existing color Variant remains editable.
   - **Overall Stock** is read-only and shows the all-branch total. A colored product also shows every
     color's total and per-branch quantities; a plain product shows its default Variant by branch.
   - **Variant Selections** — attach a shared inventory-component choice from the shop's
     library. It must not generate product/color combination rows or replace product stock.
   - **Add-ons** — a structurally separate section: attach a shared Add-on Group (e.g.
     `Extras`) or create a new one; each item (`Extra Cheese` +0.75) carries its own price
     delta. Add-ons never generate new Variant rows — picking one only changes the price of
     whichever Variant was already selected.
   - Later stock changes are made in **Inventory** through the Variant stock actions.
   - In **Inventory**, search by product, color/Variant, or Variant ID. Verify in-stock and
     out-of-stock filters use the currently selected branch, and a branch-assigned user sees
     no balances or report totals from other branches.
4. **Settings → Tax Rates** — add one rate, mark it **default** (e.g. `GST` = `0.08`,
   not inclusive).

> If you skip the menu, the POS order screen will show an empty catalog. Activation,
> staff login, and shift open/close still work without a menu.
> **Library screens:** **Variant Options** and **Add-on Groups** in the sidebar manage the
> shop-wide shared libraries directly (same groups/items products attach to in step 3).

### C5. Create staff with a POS PIN

**Users → Add User**:

| Field | Value |
|---|---|
| Full Name | `Cash One` |
| Username | `cash1` |
| Password | `cashpass1` (web login — not used on the tablet) |
| **POS PIN** | `2468` (4–6 digits) |
| Active | ✓ |

Save. Then on the user's row:

- Confirm the green **"PIN set"** badge.
- **Edit** the user → set **branch assignment** to **Central** (not "all branches").
- (You can also add a PIN later with the **Set PIN** button, or change roles under **Edit**.)

Create a second cashier `cash2` / PIN `1357` assigned to `Central` if you want the staff grid
to show more than one face.

**✓ Checkpoint:** `Users` list shows `cash1` (and `cash2`) with the **PIN set** badge.

> The **owner** (`owner1`) has all-branch access and an *Admin* role. They also appear on the
> POS staff grid but have no PIN, so they cannot PIN-sign-in until one is set.

### C6. Create a POS device → activation code

**Devices → Add Device**:

| Field | Value |
|---|---|
| Device Name | `Counter POS 1` |
| Branch | `Central` |
| Purpose | `POS` (also `Kitchen` / `Display`) |

**Create Device**. A dialog shows a **4-digit activation code** (`58 32`) with a
**15-minute** countdown, **Generate New Code**, and **Done**.

- The **"N / M devices"** counter reflects `plan.max_devices` (a no-plan tenant is capped at 1);
  hitting the cap disables **Add Device** and the API returns `409 Device limit reached`.
- Row actions: **Show code** (PENDING), **Suspend / Reactivate**, **Revoke** (permanent),
  **Delete**.

**✓ Checkpoint:** `Counter POS 1` shows status **Awaiting activation**. Keep the code for §D4.

---

### C7. Employees + Salaries (HR / payroll)

Two tenant-dashboard modules, both permission-gated. As the **Owner** (Admin role → all
permissions) you see them immediately; to test the gate, open **Roles**, tick
`employees.view` / `salaries.view` (and `…manage`) onto a role, assign it to a plain user on
**Users**, then log in as that user.

1. **Employees → Add Employee** — fill name, designation, department, monthly salary, optional
   branch. On save the row gets an auto number **`EMP-0001`** (per-tenant sequence, never
   recycled). Add a second → `EMP-0002`.
2. **Salaries** — the month/year picker defaults to the current month. The table is the
   **payroll register**: every active employee with status **unpaid / pending / paid** for that
   month. Click **Record** on an unpaid row → the drawer pre-fills base = monthly salary; add a
   bonus/deduction, **Net** updates live; **Save** (status *paid*). The KPI row shows paid vs
   pending totals, unpaid staff count and coverage %.
3. Filter **Show → Unpaid only** to get the "who hasn't been paid" list. **Print / PDF**
   (browser print dialog → Save as PDF) and **CSV** export the filtered register.
4. Back on **Employees**, the row's **This month** column now reads **Paid**.

**✓ Checkpoint:** `GET /api/v1/salaries/summary` (or the KPI row) shows `coverage` rising as you
record payments; a plain user without `salaries.view` gets the "no access" card.

> The **platform** dashboard has the same pair under **Human Resources → Employees / Salaries**
> for SaaS-company staff (auto number `PLT-0001`). Any platform admin can record payments;
> archiving an employee / deleting a payment row needs a **super admin**.

---

### C8. Attendance (clock-in/out)

A separate module from Employees — a tenant can run payroll without punch-clock tracking or
vice versa. Full reference: [`apps/backend_fastfood/docs/ATTENDANCE.md`](apps/backend_fastfood/docs/ATTENDANCE.md).

1. On **Employees**, add a test employee (or edit one) and set its own attendance PIN
   (**Set PIN**) — independent of any login. This alone is enough to clock in/out; the
   employee never needs a User account.
2. On **Users**, confirm **Add User** now picks from a dropdown of active, not-yet-linked
   employees rather than a free-typed name. Promote a *different* employee this way and
   give that new user a POS PIN (**Set PIN** on Users). This alone does **not** grant POS
   cashier access — see the `pos.operate` gate below.
3. Open **Attendance**. Pick the branch in **Currently clocked in** — empty until a punch
   happens.
4. On the POS tablet (Part D), from the staff picker tap **Clock In / Out** (works without
   signing in as a cashier). This grid lists every active employee for the branch —
   including the one from step 1 with no User at all. Select the staff member, enter their
   attendance PIN. Confirm the tile shows
   a green border and "In since HH:MM", and the dashboard's **Currently clocked in** panel
   picks it up. Tap again to clock out.
5. **`pos.operate` gate:** on **Roles**, confirm a plain custom role does **not** have
   `pos.operate` by default (existing roles were backfilled by the attendance migration, but
   a brand-new test role starts without it). With that role assigned and no `pos.operate`,
   confirm the same PIN is rejected from the ordinary staff-picker cashier login (`WHO IS
   STARTING A SHIFT?`) with a "don't have permission to operate the POS" message, while
   **Clock In / Out** still works. Grant `pos.operate` on the role and confirm cashier login
   now succeeds.
6. On the dashboard, add a **Manual entry** for an employee with no device access, then
   **Correct** an existing record (edit or clear its clock-out). Both require a reason and
   must appear in **Activity Log** under module `attendance`.

**✓ Checkpoint:** an employee with no User account at all clocks in/out successfully using
only their own attendance PIN; a promoted user without `pos.operate` clocks in/out too but
cannot open a cashier shift; Tenant B's employees/branches never appear in Tenant A's
Attendance pickers or live status.

---

## Part D — POS on the Android tablet (emulator)

### D1. One-time Flutter project setup

The repository already ships a customized, versioned `android/` project with its package,
Bluetooth permissions, icons, and release-signing enforcement. Do **not** run `flutter
create` over it. Open `apps/flutter_app_fastfood` (the directory containing
`pubspec.yaml`) in Android Studio, then run:

```powershell
cd D:\muti-saas\apps\flutter_app_fastfood
flutter doctor -v
flutter pub get
dart run build_runner build --delete-conflicting-outputs
flutter analyze
flutter test
```

> **Windows desktop:** `windows/` is already committed. `flutter run -d windows` needs
> **Developer Mode** enabled once (`start ms-settings:developers`) for plugin symlink support.
> Building the installable `.exe` + installer is **Part H** below.

**Cross-drive Gradle fix** (only if the repo is on `D:` and your Flutter pub cache is on `C:`):
`android\gradle.properties` must contain

```
kotlin.incremental=false
```

(already committed in this repo). Without it the first Android build fails with
`compileDebugKotlin ... different roots`.

### D2. Start a tablet emulator

In Android Studio open **Tools → Device Manager → Add a new device**, create a **Pixel
Tablet** AVD (API 30+, 1280×800 dp or larger), and start it with the play button. Create a
normal phone AVD such as **Pixel 7** as well, so the layout is tested at both sizes. Or use
the Flutter commands below:

PS D:\muti-saas\apps\flutter_app_fastfood> flutter emulators
2 available emulators:

Id           • Name         • Manufacturer • Platform

Medium_Phone • Medium Phone • Generic      • android
Pixel_Tablet • Pixel Tablet • Google       • android

```powershell
flutter emulators
flutter emulators --launch Pixel_Tablet
flutter devices        # note the id, e.g. emulator-5554
```

> **Minimum tablet:** 8", 1280×800, ≥ 800 dp logical width, landscape, Android 8+ (API 26+),
> 2 GB RAM.
> **Optimum:** 10–11", 1920×1200, ~1280 dp, Android 10+, 3–4 GB RAM.
> The app is **landscape-locked on mobile** (Android/iOS); on Windows the window is freely resizable.

### D3. Point the app at the backend

The emulator reaches your PC's `localhost` as **`10.0.2.2`**:

```powershell
flutter run -d emulator-5554 --dart-define=API_URL=http://10.0.2.2:8000
```

First Android build downloads the NDK/Gradle (~10–15 min, one time only).

Replace `emulator-5554` with the ID from `flutter devices`. To use Android Studio's Run
button, create a **Flutter** run configuration for `lib/main.dart` and add the
`--dart-define=API_URL=...` argument above under **Additional run args**.

### D4. Walk the flow

The app boots **landscape** and opens on the **Activation screen** when it has no saved
device activation. If this emulator was activated previously, use **Settings gear →
Deactivate this device** or clear its app data before repeating the activation test.

| # | Screen | Action | Expected |
|---|---|---|---|
| 1 | **Activation** | Type the **4-digit code** from §C6 → **Activate** | Advances to Staff. Wrong/used code → "Invalid activation code"; expired (>15 min) → "expired"; revoked device → error. |
| 2 | **Staff grid** | Tap **Cash One** → PIN pad → `2468` → **Sign in** (on desktop you can also type the PIN) | Wrong PIN → "Invalid PIN". Correct → next step. |
| 3a | **Shift open** (no open shift) | Enter **Opening cash** `200.00` → **Open shift** | Lands on Dashboard. |
| 3b | *(resume)* | If a shift is already open for this device, step 3a is skipped | Goes straight to Dashboard. |
| 4 | **Dashboard** | Greeting + shift chip ("open since HH:MM · opening Rs. 200.00"). Tap **New Order** | POS order-picker opens. |
| 5 | **Order picker** | Pick a category → a product. For a colored product choose its color SKU. When attached, **Variant Selections** are shared inventory-component choices and **Add-ons** are priced checkboxes; they remain separate. → **Add to Cart** → **View Cart** → **Take payment** → pick a tender (**Cash / JazzCash / EasyPaisa / Online Transfer / Credit Card**) → **Complete Sale** | Amounts show as `Rs. …`. Cash shows a keypad + change due; the other four charge in full and take an optional reference. Confirm only the sold color Variant's quantity decreases. (Needs the menu from C4; empty otherwise.) |
| 6 | **Dashboard → Close shift** | Enter **Counted cash** `195.00` → **Close shift** | Summary: opening `Rs. 200.00`, sales count, by-payment-method, **expected cash**, and a live **variance** (`195 − expected`). Confirm → back to Staff grid. |
| 7 | **Log out** | Dashboard → **Log out** | Back to Staff grid (device stays activated). |
| 8 | **Settings** | Dashboard → **gear icon** | Shows Shop, Branch, Device, Type, Currency; **Sync status** (Online/Offline), **Last sync**, **Sync now**, and **Deactivate this device**. |
| 9 | **Deactivate device** | Settings (or Staff footer) → admin PIN sheet | Clears activation record + device token → returns to the Activation screen. |
| 10 | **Suspend / revoke** | In the Shop dashboard **Devices** page, **Suspend** the device | Next POS sync / staff login → "device suspended" lock screen; **Reactivate** recovers it. **Revoke** → the POS wipes its token + shop context and returns to Activation (local catalog kept). |

**Persistence check:** fully close the app and relaunch → it skips the Activation screen and
opens on the **Staff grid** (shop + branch are stored locally).

**Emulator gotchas:**

- **Black screen** → the emulator display is asleep. `adb shell input keyevent KEYCODE_WAKEUP`,
  or click the emulator window.
- `flutter run` prints `Error connecting to the service protocol` then exits → adb/VM-service
  hiccup; the app still installs and runs. Launch it from the app icon, or
  `adb kill-server; adb start-server` and re-run. Hot reload needs the connection; a plain run
  does not.

---

## Part E — POS on a physical tablet or phone

### E1. Find your PC's LAN IP

```powershell
(Get-NetIPAddress -AddressFamily IPv4 |
  Where-Object { $_.InterfaceAlias -notmatch 'Loopback|vEthernet' }).IPAddress
```

Use the `192.168.x.x` / `10.x.x.x` address, e.g. `192.168.1.20`.

### E2. Make the backend reachable

- `run.py` already binds `0.0.0.0:8000`.
- Allow it through Windows Firewall (once, admin PowerShell):

  ```powershell
  New-NetFirewallRule -DisplayName "FastFood API 8000" -Direction Inbound `
    -Protocol TCP -LocalPort 8000 -Action Allow
  ```

- Phone/tablet and PC must be on the **same Wi-Fi/LAN**.

### E3. Install and run

**USB (either device, no LAN needed):**

```powershell
adb devices                       # confirm the device is listed
adb reverse tcp:8000 tcp:8000     # device localhost -> PC localhost
cd D:\muti-saas\apps\flutter_app_fastfood
flutter run -d <device-id> --dart-define=API_URL=http://localhost:8000
```

**Wi-Fi (no cable):**

```powershell
flutter run -d <device-id> --dart-define=API_URL=http://192.168.1.20:8000
```

**Standalone local-test APK to sideload:**

```powershell
flutter build apk --debug --dart-define=API_URL=http://192.168.1.20:8000
# output: build\app\outputs\flutter-apk\app-debug.apk
adb install -r build\app\outputs\flutter-apk\app-debug.apk
```

> Local testing uses a debug APK because the app rejects an HTTP `API_URL` in release mode.
> Production builds require HTTPS and the configured release keystore.

### E4. Test

Run the **Part D** table on the device. The app is landscape-locked on mobile, so hold the
tablet/phone sideways. On a phone the order-picker fits width-wise but is short vertically —
activation, staff, shift and dashboard screens are fine; `/pos` is a tablet/desktop experience.

---

## Part F — API-only test (optional, no browser/tablet)

A quick script to prove the whole chain with `curl.exe` + the venv Python. Run from
`D:\muti-saas\apps\backend_fastfood` with the server up:

```powershell
$B = "http://localhost:8000"
$PY = ".\.venv\Scripts\python.exe"

# platform login
$PT = (curl.exe -s -X POST $B/api/platform/auth/login -H "Content-Type: application/json" `
  -d '{\"email\":\"najamphysics@gmail.com\",\"password\":\"123456\"}' | & $PY -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# create shop — business_template_id is required (fetch one first: GET /api/platform/business-templates)
curl.exe -s -X POST $B/api/platform/onboarding/ -H "Authorization: Bearer $PT" -H "Content-Type: application/json" `
  -d '{\"name\":\"Demo Diner\",\"tenant_code\":\"DEMO01\",\"business_template_id\":\"<template-uuid>\",\"currency\":\"Rs.\",\"owner_name\":\"Owner One\",\"owner_username\":\"owner1\",\"owner_email\":\"o1@demo.test\",\"branch_name\":\"Central\",\"branch_code\":\"CEN\",\"trial_days\":14}'
```

Then, using the returned `owner_temp_password`, `business`/`branch` ids:

```
POST /api/v1/auth/login              {username, password, tenant_code}          -> tenant token
POST /api/v1/users/                  {username, full_name, password, pin}       -> staff (has_pin:true)
PUT  /api/v1/users/{id}/branches     {all_branches:false, branch_ids:[...]}     -> requires the 'users.manage' permission
POST /api/v1/devices                 {name, branch_id, device_type}  (Bearer tenant token)
                                       -> { ..., activation_code, activation_code_expires_at }
POST /api/v1/pos/auth/activate       {activation_code}                          -> { device_token,
                                       business_id/name, branch_id/name, currency, ... }
GET  /api/v1/pos/auth/staff          (Bearer device_token)                      -> staff list
POST /api/v1/pos/auth/staff-pin      {user_id, pin}   (Bearer device_token)     -> cashier_token
POST /api/v1/pos/session/open        {opening_cash}   (Bearer cashier_token)
GET  /api/v1/pos/session/summary                       (Bearer cashier_token)
POST /api/v1/pos/session/close       {closing_cash}    (Bearer cashier_token)   -> {session, summary, variance}
GET  /api/v1/pos/sync/full                             (Bearer cashier_token)   -> includes "currency"
# suspend from the tenant side, then watch the guard bite:
POST /api/v1/devices/{id}/suspend    (Bearer tenant token)
GET  /api/v1/pos/sync/full           (Bearer cashier_token)   -> 403 {code:"DEVICE_SUSPENDED"}
```

---

## Part G — Reset between test runs

**Full backend reset:**

```powershell
# stop run.py first (Ctrl+C)
psql -U postgres -c "DROP DATABASE fastfood_test;"
psql -U postgres -c "CREATE DATABASE fastfood_test OWNER account_admin;"
cd D:\muti-saas\apps\backend_fastfood
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe scripts\bootstrap_platform.py
.\.venv\Scripts\python.exe run.py
```

**Device reset (clear activation without wiping the app):** in the app,
**Settings → Deactivate this device** (then add the device again in the Shop dashboard for a
fresh code). Or from adb:

```powershell
adb shell pm clear com.fastfood.fastfood_pos
```

On Windows the local state lives in `%APPDATA%\com.example\fastfood_pos\` (Drift DB) and the
Windows Credential Manager (device token) — delete those to reset.

---

## Part H — Building release artifacts (Windows exe, installer, production APK)

Everything above runs the app via `flutter run` — debug/profile, hot-reload, no installable
file. To hand someone a real file — for LAN testing without a dev machine attached, for the
office desktop, or for going live — build a release artifact instead.

### H1. Windows desktop — `.exe` + installer

```powershell
cd D:\muti-saas\apps\flutter_app_fastfood
flutter build windows --release --dart-define=API_URL=http://localhost:8000
# output: build\windows\x64\runner\Release\smart_shop.exe  (+ its DLLs + a data\ folder)

"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" installer\smart_shop.iss
# output: installer\dist\SmartShop-Setup-<version>.exe   — single file, per-user, no admin
```

Requires [Inno Setup 6](https://jrsoftware.org/isdl.php) installed once (free). Run the
resulting `SmartShop-Setup-<version>.exe` to install for real (Start Menu + optional desktop
shortcut) — or just launch the `.exe` straight out of the `Release` folder for a quick check
without installing anything.

### H2. Android — APK for a tablet/phone

Already covered above in **Part E3** for LAN testing (`flutter build apk --debug
--dart-define=API_URL=http://<your-PC-LAN-IP>:8000`, then `adb install -r ...apk`). A build
you hand out more widely must instead be a signed release build pointed at the live HTTPS API;
follow [`deploy/DEPLOYMENT-RUNBOOK.md`](deploy/DEPLOYMENT-RUNBOOK.md) §4.2.

### H3. Which `API_URL` to bake in

The address is compiled into the binary — it is not a setting you can change after install.
Picking the wrong one means a reinstall, not a config edit. `lib/core/network/dio_client.dart`
defaults to `http://10.0.2.2:8000` (the Android-emulator-only loopback alias) whenever
`--dart-define=API_URL=...` is left off the build command.

| Target | `--dart-define=API_URL=` | Documented in |
|---|---|---|
| Android **emulator** | *(omit it — the default already works)* | Part D3 |
| Physical tablet/phone, **same Wi-Fi as your PC** | `http://<your-PC-LAN-IP>:8000` (found in Part E1) | Part E3 |
| Windows desktop, **same machine as the backend** | `http://localhost:8000` | H1 above |
| Any of the three against the **live SaaS cloud** | `https://<your-domain>` | going live, next |

### H4. Going live

This guide covers a single local workstation end to end. For a real server and distributable
installers, continue with the single
[`deploy/DEPLOYMENT-RUNBOOK.md`](deploy/DEPLOYMENT-RUNBOOK.md). It covers the production
domain, SMTP, CORS, `.env`, migrations, VPS/nginx/systemd/HTTPS, client builds, rollout,
verification, backups, and rollback.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `alembic : term not recognized` | venv not on PATH | Call `.\.venv\Scripts\python.exe -m alembic …` or activate the venv (see §0). |
| `Activate.ps1 cannot be loaded … scripts is disabled` | PowerShell execution policy | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` (this session), or `-Scope CurrentUser -ExecutionPolicy RemoteSigned` (permanent, no admin). |
| `connection refused` / `Socket is not connected` on startup | PostgreSQL not running, or wrong `DATABASE_URL` | Start PostgreSQL; verify DB name/host/port in `.env`. |
| `alembic current` prints nothing | migrations never applied to this DB | `alembic upgrade head`. |
| Platform login 401 | wrong creds or admin not bootstrapped | Re-run `bootstrap_platform.py`; password = `.env` `PLATFORM_ADMIN_PASSWORD`. |
| Tenant login "Field required: tenant_code" | shop code missing | Include the Tenant/Shop Code (`DEMO01`) on the tenant login form / payload. |
| POS: "Invalid activation code" | wrong / already-used code | Generate a fresh code in the Shop dashboard **Devices** page. |
| POS: "This activation code has expired" | > 15 minutes since it was issued | **Generate New Code** in the dialog (or the device row → **Show code**). |
| POS: "Device limit reached" when adding a device | tenant at `plan.max_devices` (or the 1-device no-plan cap) | **Revoke** an unused device, or assign a bigger plan. |
| POS shows a "device suspended / revoked" screen | platform or tenant suspended/revoked it | **Reactivate** it in the dashboard (a *platform* suspension can only be lifted by the platform). |
| Tablet: staff grid empty | staff not assigned to this branch, or inactive | In Users, set the cashier's branch assignment to the selected branch; ensure Active. |
| Tablet: "Invalid PIN" for a known-good PIN | PIN never set / mismatch | Users → **Set PIN**; confirm the "PIN set" badge. |
| Order screen shows empty catalog | no menu synced | Build the menu (§C4); on the tablet **Settings → Sync now**. |
| Amounts show `$` instead of `Rs.` | currency not synced yet | Save Currency in shop Settings, then **Sync now** on the POS (or deactivate + re-activate the device). |
| `AndroidManifest.xml could not be found` on `flutter run` | The customized tracked `android/` project is missing, or the wrong directory is open | Restore `apps/flutter_app_fastfood/android` from the same Git release and open the folder containing `pubspec.yaml`; do not regenerate it with `flutter create`. |
| First Android build fails: `compileDebugKotlin … different roots` | project on `D:`, pub cache on `C:` | `kotlin.incremental=false` in `android/gradle.properties` (already set). |
| Emulator all black | display asleep | `adb shell input keyevent KEYCODE_WAKEUP`, or click the emulator. |
| `flutter run` exits with `Error connecting to the service protocol` | adb/VM-service hiccup | App still runs — launch from the icon; `adb kill-server; adb start-server` and retry for hot reload. |
| Physical device can't reach the API | firewall / wrong IP / different network | Open TCP 8000 inbound; use the PC LAN IP; same Wi-Fi; or `adb reverse tcp:8000 tcp:8000` over USB with `API_URL=http://localhost:8000`. |
