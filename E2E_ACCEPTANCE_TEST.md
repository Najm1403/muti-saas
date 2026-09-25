# Full local acceptance test: platform → tenant → POS

Use this workflow locally and repeat the release-critical cases against staging after
deployment. The ordered production and post-deployment commands are in
[`deploy/DEPLOYMENT-RUNBOOK.md`](deploy/DEPLOYMENT-RUNBOOK.md).

Use this test on a fresh local database before deployment. It verifies the complete path from platform administration through tenant configuration to Windows desktop and Android POS clients.

## 0. Required software and files

- PostgreSQL 14+
- Python 3.11+
- `apps/backend_fastfood/.venv` with `requirements.txt` installed
- Flutter SDK, Android Studio/JDK 17, and an Android emulator or device
- Visual Studio 2022 with **Desktop development with C++**
- Chrome or Edge
- Repository files: `apps/backend_fastfood/.env`, `apps/web_fastfood`, and `apps/flutter_app_fastfood`

For detailed setup, use [LOCAL TESTING GUIDE.md](LOCAL%20TESTING%20GUIDE.md). For client build commands, use [BUILD_CLIENTS.md](apps/flutter_app_fastfood/BUILD_CLIENTS.md).

## 1. Start with a clean local backend

Create a disposable test database, point `.env` at it, then run:

```powershell
cd D:\muti-saas\apps\backend_fastfood
.\.venv\Scripts\Activate.ps1
$env:DEBUG='false'
python -m alembic upgrade head
python scripts/bootstrap_platform.py
python run.py --host 0.0.0.0 --port 8000
```

Verify these URLs before continuing:

- `http://localhost:8000/health`
- `http://localhost:8000/ready`
- `http://localhost:8000/docs`
- `http://localhost:8000/platform/login.html`

Run the automated backend gate in a second terminal:

```powershell
cd D:\muti-saas\apps\backend_fastfood
$env:DEBUG='false'
pytest -q
```

Do not continue toward release if this fails.

## 2. Platform dashboard test

1. Log in at `/platform/login.html` as the platform super administrator.
2. Open **Business Templates** and create or select two active templates: one Fast
   Food-style (optional quantity tracking) and one Electronics-style
   (shows optional cost price and forces quantity inventory tracking) — the **Load
   Fast Food preset** / **Load Laptop Business preset** buttons fill in a working `config` for
   each. Each seeds its own starting categories and shared Variant Option Groups / Add-on
   Groups (verify these show up under §3.2 below).
3. Create two test tenants: `TENANT_A` (Fast Food template) and `TENANT_B` (Electronics
   template) via **Create Tenant** — the **Business Template** dropdown is required.
4. Give each tenant a separate branch and owner account.
5. On Tenant A's Business Template, uncheck a module (e.g. Kitchen Stations) in the
   editor's checkbox grid and save. Verify `config.modules.hidden` now contains that key.
6. Open Tenant A's Modules tab (read-only) and confirm the hidden module shows struck
   through, with a link back to the template's editor.
7. Open Tenant B's Modules tab and confirm it is unaffected (different template).
8. As Tenant A's owner, confirm the hidden module's sidebar link is gone and its API
   routes 403 with `code: "MODULE_DISABLED"`.
9. Try saving Tenant A's Business Template with a mandatory module (e.g. `settings`) in
   `modules.hidden` — confirm the API rejects it (422).
10. Re-check the module and save. Confirm it reappears for Tenant A.
11. Confirm a non-super platform admin can view Business Templates but cannot create,
    edit, or delete them (the New/Save/Delete controls are hidden or disabled).

**Important:** module visibility now lives entirely on the Business Template — there is no
per-tenant override, so editing it on **Platform → Business Templates** affects every
tenant on that template at once. Business-template editing is only ever selected once, at
onboarding (§3, above) — there is no "switch a tenant to a different template" flow, since
a tenant's product/pricing model is not meant to change after the shop has real data. A
tenant administrator can manage only its own tenant and must never be able to select
another tenant.

## 3. Tenant dashboard data test

For each tenant, log in through `/tenant/login.html` and configure only that tenant:

1. Create a category and a plain product with a distinctive name, **Sale Price**, and
   opening stock. Then create a colored product: select two Colors in **Add Product** and
   enter each color's own Sale Price and opening stock. Colors are create-time SKUs, not
   labels or add-ons. On the Electronics tenant, confirm Cost Price is visible but optional.
2. Open the product's detail page:
   - Confirm existing color Variant prices are editable and color membership remains the
     create-time selection from Add Product.
   - Confirm **Overall Stock** shows the product total across branches. For the colored
     product it must also show every color's total and per-branch quantities.
   - Attach a **Variant Selection** group (from the template-seeded shared library, or
     create one) and confirm it remains a shared inventory-component choice; it must not
     generate color combinations or replace the product's own stock.
   - Separately, attach an **Add-on Group** (e.g. Toppings / Extended Warranty) with priced
     items, at least one marked **default selected**. Confirm this section never affects the
     product/color stock above.
3. Add a tax rate, a deal, and a promotion.
4. Create a cashier, assign it to the test branch, and set a POS PIN.
5. Create one POS device on that branch and record its one-time activation code.
6. Grant the cashier Free Guest permission; later revoke it to test both states.
7. Create a second staff user, set a PIN, but leave their role without `pos.operate`.
   Confirm they cannot cashier-login on the POS (rejected with `POS_ACCESS_DENIED`) but
   can still use **Clock In / Out**. The full acceptance script is
   [`apps/backend_fastfood/LOCAL_TESTING.md`](apps/backend_fastfood/LOCAL_TESTING.md) §8
   and [`apps/backend_fastfood/docs/ATTENDANCE.md`](apps/backend_fastfood/docs/ATTENDANCE.md).
8. Repeat with different values for Tenant B so cross-tenant leakage is obvious — including
   confirming Tenant A's shared Variant Option Groups / Add-on Groups never appear when
   editing a Tenant B product, and Tenant A's attendance register/live-status never shows
   Tenant B's employees.

## 4. Windows POS test

Build or run against the local API:

```powershell
cd D:\muti-saas\apps\flutter_app_fastfood
flutter pub get
dart run build_runner build --delete-conflicting-outputs
flutter run -d windows --dart-define=API_URL=http://localhost:8000
```

1. Activate using Tenant A’s device code.
2. Confirm the shop and branch shown belong to Tenant A.
3. Sign in as Tenant A’s cashier and open a shift.
4. Confirm the distinctive product, color prices, tax, deal, and promotion appear. Open its
   customization panel and confirm Color SKU, Variant Selection component, and Add-on are
   visually separate, with the default-selected Add-on pre-ticked.
5. Add the product with a non-default Color, one Variant Selection, and at least one Add-on
   (with one default Add-on unticked). Confirm the product/color and linked component are
   distinct cart/stock lines and the total is correct, then test Cash, JazzCash, EasyPaisa, Online Transfer,
   and Credit Card as applicable.
6. With Free Guest granted, confirm the option appears; revoke permission in the tenant dashboard, sync, and confirm it disappears.
7. Suspend the device in the tenant dashboard. Trigger sync and verify the POS locks.
8. Reactivate the device and verify it recovers after sync.
9. Create an offline sale, stop the API, complete the sale, restart the API, sync, and verify the sale uploads once.
10. Change the product price in the tenant dashboard, press **Sync now**, and verify the POS shows the new price.

## 5. Android tablet and phone test

Emulator:

```powershell
flutter run -d emulator-5554 --dart-define=API_URL=http://10.0.2.2:8000
```

Physical device on the same Wi-Fi:

```powershell
flutter run -d <device-id> --dart-define=API_URL=http://<PC-LAN-IP>:8000
```

Repeat every Windows POS test on the tablet. Also check:

- Landscape tablet layout and phone layout.
- Keyboard/PIN input and touch keypad.
- App restart preserves activation and branch context.
- Sync status and last-sync timestamp update.
- Offline sale recovery after reconnect.
- Tenant B’s activation code cannot activate a Tenant A device.

## 6. Isolation and freshness sign-off

The test passes only when all statements are true:

- Tenant A never sees Tenant B’s products, users, branches, devices, sales, or settings.
- Each POS only receives the branch and tenant encoded by its device token.
- Dashboard edits reach both POS clients after a manual sync and within the five-minute background interval.
- Deletions/deactivations disappear after sync.
- Free Guest permission is enforced per cashier and cannot be used offline.
- Offline sales upload exactly once after reconnection.
- Online and offline sales retain their cashier and shift attribution; tenant Sales and
  the applicable Reports panels honor combined date, cashier, and shift filters.
- POS Reports remains usable from retained SQLite data while offline, does not duplicate
  a sale after upload, and never deletes an unsynced sale during retention cleanup.
- Suspended/revoked devices are blocked server-side.
- An employee's own attendance PIN clocks in/out with no `User` account or `pos.operate`
  needed at all; a `User` promoted from an employee but without `pos.operate` is rejected
  from cashier login. Attendance records and live status never cross tenants.

## 7. Release candidate checks

After the local acceptance test passes:

```powershell
cd D:\muti-saas\apps\flutter_app_fastfood
flutter analyze
flutter test
flutter build windows --release --dart-define=API_URL=https://shop.apkaysoftware.com
flutter build apk --release --dart-define=API_URL=https://shop.apkaysoftware.com
flutter build appbundle --release --dart-define=API_URL=https://shop.apkaysoftware.com
```

The HTTPS builds must be tested against the real API before distribution. Android release signing and a production database are mandatory; local HTTP builds are for local testing only.
