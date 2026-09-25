# POS desktop and Android build guide

The Windows desktop and Android clients use the same Flutter codebase and the same tenant-scoped API. Build-time `API_URL` is compiled into the app; changing the server later requires a new build.

Use [`../../deploy/DEPLOYMENT-RUNBOOK.md`](../../deploy/DEPLOYMENT-RUNBOOK.md) for the
complete release order, backend readiness checks, artifact hashes, production smoke
tests, backup, monitoring, and rollback. This document is the client-specific guide.

## Data flow and freshness

Tenant-admin catalog changes flow through the backend POS sync endpoints:

1. Tenant admin saves products, categories, prices, stock, tax rates, deals, or promotions.
2. The POS calls `GET /api/v1/pos/sync/full` using its persistent device token; catalog sync does not require a cashier to be signed in.
3. The app replaces its local Drift catalog transactionally and records the server cursor.
4. The background sync runs at launch, immediately after activation and cashier sign-in, every five minutes, after connectivity returns, and when the cashier presses **Retry** or uses **Settings > Sync now**.
5. The menu repository is invalidated after a successful sync so the POS reads the refreshed local catalog.

Sales go in the opposite direction through the cashier-authenticated offline outbox and are uploaded when connectivity returns. Catalog sync and heartbeat use the device token; shift, sale, and outbox-upload operations use the cashier token. A failed sync is shown as **Sync needs attention** instead of being silently ignored. Free Guest permission is checked online for the active cashier and fails closed when the permission endpoint cannot be reached; it is intentionally not cached as an offline entitlement.

The supported client includes the active shift `session_id` in every checkout. Confirmed
online receipts and queued offline sales are both cached in SQLite for date-, cashier-,
and shift-filtered reports when the server is temporarily unavailable. Synced history is
eligible for cleanup after 90 days (up to 1,000 rows are rendered in the POS report);
unsynced sales are never removed by retention. See
[`../backend_fastfood/docs/SALES_AND_REPORTING.md`](../backend_fastfood/docs/SALES_AND_REPORTING.md)
for filter scope, cloud/local merge behavior, exact limits, and tests.

The POS catalog search matches product names/codes, option-group names, option
values, and composed variant names. Multi-word searches such as `4 GB RAM`
match the combined variant description. The order picker always exposes a
**Dashboard** action. Cash checkout starts at the amount due, accepts desktop
keyboard or on-screen keypad input, and cannot complete below the due amount.

Device activation binds a client to one tenant and branch. The API derives scope from the device or cashier token, so a client cannot request another tenant's catalog or upload sales to another tenant or branch.

Inventory belongs to concrete Variants: the product's default/color SKU and any
separately linked component Variant. Each has integer per-branch balances and its own
tracking flag. Product branch assignments control visibility independently of stock.
Variant Selections resolve to their component product's Variant; they never synthesize a
host-product combination.

Inventory sync version **5** carries `allow_inventory_tracking` on each variant.
Stock checks and deductions require both that gate and `tracks_inventory`.
Untracked variants remain sellable. Product and selected component Variants are
independent stock lines. Checkout aggregates cart lines by Variant before validation.
Offline reservations share the outbox
transaction; upload pending sales before replacing a stock snapshot.
Disconnected devices can still compete for the same stock, so the server
validates each upload and shortages require reconciliation.

Apply every pending backend migration using `python -m alembic upgrade head`
from `apps/backend_fastfood`. Never hardcode a revision copied from documentation.
Deploy the compatible backend before distributing updated clients, then perform a full
menu sync.
Regenerate serializers with `dart run build_runner build --delete-conflicting-outputs`
when changing sync models.

**Add Product** owns color selection plus each color's sale price and one-time opening
stock. Product detail shows read-only overall/color/branch totals and permits price edits,
but never adds colors. **Inventory** lists eligible Variants and uses only the Variant stock
routes for Increase, Decrease, Set Stock, and History. Inventory is quantity-only.
Refunds restore only previously deducted lines whose two current toggles are on;
either toggle being off skips restoration without an error. Every stock action,
sale, cancellation, and return writes an audit row. Free Guest orders have no paid
amount and cannot produce a cash refund.

### Bill cancellation and sales returns

For the complete cashier procedure, accounting behavior, stock rules, error recovery,
and manager acceptance checklist, see
[POS bill cancellation and sales returns](../backend_fastfood/docs/POS_RETURNS_AND_CANCELLATIONS.md).

These are separate, online-only accounting operations and both require the cashier's
role to include `sales.cancel`:

- **Cancel Order / Bill** appears on the completed receipt and in **Recent
  transactions**. It reverses the complete bill, is allowed only for the cashier and
  device that created it while that same shift remains open, requires a reason, restores
  eligible tracked stock, and changes the sale to `CANCELLED`.
- **Sales Return** is a dashboard feature. Enter the exact printed Invoice ID, select
  returned items and quantities, and confirm. The server derives the refund from the
  immutable original sale prices; the client cannot choose a refund amount. Partial
  returns leave the sale completed, while returning every remaining item changes it to
  `REFUNDED`.

The shift close/history screens and their PDFs report later returns separately from
same-shift cancelled bills. Do not attempt either operation while offline: offline sale
upload remains supported, but financial reversals intentionally require the server to
lock and validate the current invoice state.

### Promotions and deals

Tenant setup, field meanings, worked examples, branch assignment, POS application, and
troubleshooting are documented in
[Creating promotions and deals](../backend_fastfood/docs/PROMOTIONS_AND_DEALS.md).

See [the inventory guide](../backend_fastfood/docs/INVENTORY.md)
for deployment, rollback, and verification steps.

## Prerequisites

- Flutter SDK matching the repository's Dart constraint (`>=3.3.0 <4.0.0`).
- Android SDK and an Android emulator/device for APK testing.
- Visual Studio with **Desktop development with C++** for Windows builds.
- A running backend with migrations applied and a reachable PostgreSQL database.
- A tenant device activation code generated in the tenant dashboard.

The Android host project contains customized Bluetooth permissions, icons, package
configuration, and release-signing enforcement. It must be committed as non-secret
source and restored by a clean clone. Do not regenerate it with `flutter create` during
a release. The repository root currently has a broad ignore rule for `android/`; remove
that rule before release while keeping `key.properties`, `local.properties`, build
caches, and keystores ignored. Never use `git add -f android`, because that can include
secrets and machine-local files.

## Prepare the project

From `apps/flutter_app_fastfood`:

```powershell
flutter pub get
dart run build_runner build --delete-conflicting-outputs
flutter analyze
flutter test
```

## Local Windows desktop build

Start the backend locally first, then build with the API URL reachable from the desktop:

```powershell
flutter run -d windows --dart-define=API_URL=http://127.0.0.1:8000
```

Do not use localhost for a distributable release. After development and testing succeed,
and after the public HTTPS API passes its health check, create the optimized Windows
release build with the real domain:

```powershell
Set-Location D:\muti-saas\apps\flutter_app_fastfood
flutter build windows --release --dart-define=API_URL=https://YOUR.DOMAIN
```

The executable is under `build\windows\x64\runner\Release\`. Copy the entire Release directory when testing; the executable depends on its bundled DLLs and data directory.
To create the installer, install Inno Setup 6 and run:

```powershell
& "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" installer\smart_shop.iss
```

The installer is written to `installer\dist\`.

## Printer support

Receipts and shift summaries use the operating-system print dialog. Standard
Windows laser, inkjet, USB, and network printers work after they are installed
in Windows. Use **Settings > Printer > Open printer / Print test page** to
verify the configured driver.

Each POS device stores its own receipt format under **Settings > Printer >
Receipt print and PDF format**:

- **A4 - desktop / laser printer** creates the full-page branded invoice.
- **80 mm - thermal receipt printer** creates a narrow roll receipt with a
  content-based paper length.

The selection is used by both **Print** and **PDF/Share** and remains saved
after the app is restarted. A4 is the default for existing installations.

On Android, printers exposed by Android's print framework are supported, and
80 mm Bluetooth printers can also use direct ESC/POS mode. Both live and
historical shift summaries provide **Print** and **Save PDF**.

### Speed-X / Bluetooth 80 mm setup

1. Turn on the Speed-X printer and load 80 mm paper.
2. Pair it in Windows **Bluetooth & devices** or Android **Connected devices**.
   Use the PIN documented by the printer (commonly `0000` or `1234`).
3. In the POS open **Settings > Printer**.
4. Select **80 mm - thermal receipt printer** and **Direct Bluetooth ESC/POS**.
5. Press **Scan paired Bluetooth printers**, select the Speed-X device, then
   press **Connect and print Bluetooth test receipt**.

The selected printer address is saved locally. Later sales reconnect and print
directly from the receipt screen. On Android 12 or newer, approve the **Nearby
devices** permission when requested. Location access is not used.

Windows Bluetooth printers vary by transport. Direct mode supports printers
that expose a writable Bluetooth Low Energy service. If a Speed-X model uses
Bluetooth Classic/Serial Port Profile and is not listed by direct scan, install
its Windows printer driver, add it under **Printers & scanners**, then select
**System printer driver / dialog** in the POS. The same branded 80 mm layout is
used through the Windows print spooler.

Keep the printer disconnected from other phones/tablets while testing; many
low-cost Bluetooth thermal printers accept only one active connection.

## Android emulator testing

### First run from Android Studio

The repository already contains a customized `android/` project. Do **not** run
`flutter create` over it. That can replace the package, permissions, icons, and release
signing rules.

1. Start the local backend and confirm `http://127.0.0.1:8000/health` works on the PC.
2. In Android Studio, open `apps/flutter_app_fastfood` (the folder containing
   `pubspec.yaml`), not the `android` subfolder. Let Gradle/Flutter indexing finish.
3. Open **Tools > Device Manager > Add a new device**. Create both a **Pixel Tablet**
   and a normal phone such as **Pixel 7**, using an API 30 or newer system image. Start
   one virtual device with its play button.
4. Open Android Studio's **Terminal** and run the preparation commands below. Check
   `flutter devices` and copy the running emulator ID.
5. Use the terminal launch command below for the first real-flow test. This is safer
   than Android Studio's plain Run button because the required API URL and real-flow
   flag are visible in the command.

```powershell
Set-Location D:\muti-saas\apps\flutter_app_fastfood
flutter doctor -v
flutter pub get
dart run build_runner build --delete-conflicting-outputs
flutter devices
flutter run -d emulator-5554 --dart-define=API_URL=http://10.0.2.2:8000
```

Replace `emulator-5554` with the ID printed by `flutter devices`. The Android emulator
reaches the host computer through `10.0.2.2`; `localhost` inside the emulator means the
emulator itself. The first Gradle build can take several minutes. Once connected, use
`r` in the terminal for hot reload and `R` for a hot restart.

If you prefer Android Studio's Run button, create a **Flutter** run configuration with
`lib/main.dart` as the Dart entrypoint and put this in **Additional run args**:

```text
--dart-define=API_URL=http://10.0.2.2:8000
```

Select the running phone/tablet in the device selector and press **Run**. The current
debug and release builds both start at the real activation/authentication flow.

For a directly installable local-test APK, use a **debug** build because release builds
intentionally reject HTTP API URLs:

```powershell
flutter build apk --debug --dart-define=API_URL=http://10.0.2.2:8000
adb install -r build\app\outputs\flutter-apk\app-debug.apk
```

For a physical tablet or phone on the same Wi-Fi, use the computer's LAN address instead, for example `http://192.168.1.20:8000`, and allow port 8000 through the local firewall.

### Thorough phone and tablet test pass

Run the end-to-end acceptance test below on both AVDs. In addition, verify:

- No text is clipped or unreachable on the phone and tablet in landscape; test the
  smallest supported screen and the intended shop tablet resolution.
- Activation survives a force-stop and restart, while **Deactivate this device** clears
  it. Also test wrong, expired, suspended, and revoked activation states.
- Wrong cashier PINs and users without `pos.operate` are rejected; opening cash, shift
  resume, logout, close-shift totals, and variance are correct.
- Product search, variants, add-ons, discounts/tax, every enabled payment method,
  receipt/PDF output, cash change, cancellation, partial return, and full return work.
- Turn off emulator Wi-Fi, make a permitted offline sale, restart the app, reconnect,
  and confirm the outbox uploads exactly once and stock/reporting reconcile correctly.
- Change price, stock, tax, promotion, and product visibility in the tenant dashboard;
  use **Settings > Sync now** and also verify automatic sync after reconnect.
- A second tenant and branch never appear in this device's staff, catalog, inventory,
  sales, or reports. This is a release-blocking isolation check.
- If the deployment uses a Bluetooth printer, repeat printing on a real Android device;
  an emulator cannot validate Bluetooth pairing, permissions, or paper output.

Use `adb logcat` or Android Studio's **Logcat** window while reproducing any crash. Take
a fresh activation code when resetting app data, because an activation code is one-use.

## Release APK

Release builds require a permanent unique `applicationId` and an Android signing key.
Before the first public release, replace `com.fastfood.fastfood_pos` in
`android/app/build.gradle.kts`; a Play Store application ID cannot be changed after
publication. Create a private keystore outside the repository, back it up securely,
configure `android/key.properties` locally, and ensure both files are ignored by Git.
Then build against an HTTPS API from `D:\muti-saas\apps\flutter_app_fastfood`:

```powershell
Set-Location D:\muti-saas\apps\flutter_app_fastfood
flutter build apk --release --dart-define=API_URL=https://YOUR.DOMAIN
```

For store distribution, use an app bundle instead:

```powershell
Set-Location D:\muti-saas\apps\flutter_app_fastfood
flutter build appbundle --release --dart-define=API_URL=https://YOUR.DOMAIN
```

Never ship a release build with `http://`, an emulator URL, a development database, or development credentials. The app rejects release builds unless `API_URL` is explicitly HTTPS.

## From local testing to the online SaaS

The canonical commands and rollback procedure are in
[`../../deploy/DEPLOYMENT-RUNBOOK.md`](../../deploy/DEPLOYMENT-RUNBOOK.md). Use this order:

1. Finish the automated and manual checks in this document. Commit every intended
   source file and Alembic migration, create a release tag, and record its commit SHA.
2. Provision the Ubuntu/VPS host, PostgreSQL, DNS record, firewall, nginx, systemd, and
   TLS certificate as described in runbook §3. Expose only SSH and nginx publicly; keep
   PostgreSQL and backend port 8000 private.
3. On the server, check out the exact release tag, install backend dependencies, create
   the production `.env`, and run `python -m alembic upgrade head`. Use
   `ENVIRONMENT=production`, `DEBUG=false`, a stable secret key, the production database,
   exact HTTPS CORS origin, and working SMTP credentials.
4. Do not build clients yet. First verify the deployed server and web dashboards:

   ```text
   https://YOUR.DOMAIN/health
   https://YOUR.DOMAIN/platform/login.html
   https://YOUR.DOMAIN/tenant/login.html
   ```

5. Back on the Windows build workstation, configure the permanent Android application
   ID and protected signing keystore. Build the APK/AAB with
   `--dart-define=API_URL=https://YOUR.DOMAIN` using the commands above. The domain must
   be the API origin, with no `/docs` or dashboard path appended.
6. Record SHA-256 hashes, install the signed APK on a clean real tablet, activate it with
   production test data, and repeat the critical online/offline, sync, payment, receipt,
   printer, tenant-isolation, cancellation, and return checks.
7. Enable backups and monitoring before onboarding real tenants. Keep the previous server
   release and client artifact available; database rollback is a restore procedure, not
   an automatic Alembic downgrade.

Do not point a production client at a local or staging database. Because `API_URL` is
compiled into the app, moving to another domain requires rebuilding and reinstalling the
client.

## End-to-end acceptance test

1. Activate one Windows client and one Android client to the same branch.
2. Change a product name, price, active flag, stock, promotion, or tax rate in the tenant dashboard.
3. Trigger **Sync now** on both clients and confirm the new value appears.
4. Wait five minutes or reconnect one device and confirm automatic sync.
5. Confirm a second tenant's device still sees its own catalog.
6. Disable Free Guest for the cashier and verify the payment option disappears; grant it again and verify it returns after the permission refresh.
7. Create an offline sale, reconnect, and confirm it appears in the tenant dashboard once without duplication.
8. Create a colored product with separate price/opening stock for each color, sync both clients, and confirm the same Variant stock appears on each device.
9. Sell one color online and offline. Confirm server stock decreases once for only that color and the offline client updates its local balance immediately.
10. Attempt an over-stock sale with negative stock disabled, then enable that Variant's negative-stock policy and confirm the behavior changes only for that Variant.
11. Complete a bill, use **Cancel Order / Bill** before closing the shift, and confirm the bill becomes `CANCELLED`, its tracked stock is restored, and the cancellation is shown separately at shift close.
12. Close the shift, open another shift, use **Sales Return** with the old Invoice ID, return one item, and confirm only that quantity and its server-calculated amount are returned.
13. Attempt to cancel the old-shift bill, exceed the remaining return quantity, repeat a completed return, and perform either action without `sales.cancel`; confirm every attempt is rejected.

## Required validation before packaging

From the Flutter project directory, run:

```powershell
dart run build_runner build --delete-conflicting-outputs
flutter analyze
flutter test
```

From the backend project directory, run:

```powershell
$env:ENVIRONMENT='development'
$env:DEBUG='false'
alembic upgrade head
pytest -q
```

The expected baseline is no analyzer issues, all Flutter tests passing, and
the complete backend suite passing. Do not package clients until all three
checks complete successfully.
