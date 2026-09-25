# Storixx POS

Offline-first Flutter POS app for branch cashiers — device activation (4-digit code),
staff PIN sign-in, shift open/close, order taking, Take Payment (Cash / JazzCash /
EasyPaisa / Online Transfer / Credit Card), receipts, and background sync against the
`backend_fastfood` API. Runs on Android tablet/phone and Windows desktop from one codebase.

## Where things are documented

This app is one piece of a larger platform — its setup, build, and release steps live in the
repo-root docs, not here, so there is a single source of truth:

- **[`../../LOCAL TESTING GUIDE.md`](../../LOCAL%20TESTING%20GUIDE.md)** — run the whole stack
  (backend + dashboards + this app) on one machine. Part D = Android emulator, Part E = a real
  tablet/phone, **Part H = building the release `.exe` / installer / APK**.
- **[`ACTIVATION_CONTRACT.md`](ACTIVATION_CONTRACT.md)** — the device-activation request/response
  contract (`POST /api/v1/pos/auth/activate`).
- **[`../../deploy/DEPLOYMENT-RUNBOOK.md`](../../deploy/DEPLOYMENT-RUNBOOK.md)** — going live:
  production configuration, rebuilding clients against HTTPS, signing, distribution,
  verification, and rollback.
- **`installer/smart_shop.iss`** — the Inno Setup script that packages the Windows build into
  `installer/dist/SmartShop-Setup-<version>.exe`.

The sales/reporting contract, including date/cashier/shift filters, the cloud/SQLite
merge, limits, retention, and tests, is documented in
[`../backend_fastfood/docs/SALES_AND_REPORTING.md`](../backend_fastfood/docs/SALES_AND_REPORTING.md).

## Quick reference

```powershell
flutter pub get
dart run build_runner build --delete-conflicting-outputs

# run against the local backend (Android emulator)
flutter run -d emulator-5554 --dart-define=API_URL=http://10.0.2.2:8000

# local Android APK (HTTP is allowed only in debug mode)
flutter build apk --debug --dart-define=API_URL=http://<host>:8000

# production release builds — use the live HTTPS API and configured signing key
flutter build apk     --release --dart-define=API_URL=https://<your-domain>
flutter build windows --release --dart-define=API_URL=https://<your-domain>
"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" installer\smart_shop.iss
```

`API_URL` is compiled in at build time (default `http://10.0.2.2:8000`, the Android-emulator
loopback) — see `lib/core/network/dio_client.dart`. Getting it wrong means a reinstall, not a
setting to flip.
