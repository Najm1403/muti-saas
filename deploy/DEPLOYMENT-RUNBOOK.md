# Production deployment runbook

This is the canonical checklist for deploying the SaaS web application, FastAPI
backend, PostgreSQL database, and Flutter POS clients. Do not treat a successful
Flutter compile as a completed deployment: the public HTTPS backend must be
running and verified before production clients are built.

The commands below assume:

- Windows source checkout: `D:\muti-saas`
- Ubuntu server checkout: `/var/www/multi-saas`
- systemd unit: `multi-saas`
- nginx site: `multi-saas`
- backend port: `127.0.0.1:8000`

Replace every value written as `YOUR.DOMAIN`, `YOUR_EMAIL`, `YOUR_REPOSITORY`,
or `CHANGE_ME`. Do not type angle brackets into a command or configuration
value.

## 1. Release decision gate

Do not deploy until every applicable item is resolved:

- All intended source files and Alembic migrations are reviewed, committed,
  pushed, and included in the release tag. An untracked migration will never
  reach a server through `git pull`.
- The complete backend, web smoke, and Flutter test gates below pass.
- `alembic heads` prints exactly one head.
- Production uses `ENVIRONMENT=production`, `DEBUG=false`, a stable random
  `SECRET_KEY`, a production PostgreSQL database, and an exact HTTPS
  `CORS_ORIGINS` value. `DEBUG=release` is invalid; use `false`.
- DNS, TLS, SMTP, database backups, media backups, monitoring, and restore
  ownership are assigned.
- Android has a permanent unique application ID and a protected release
  keystore. Never publish the generic `com.fastfood.fastfood_pos` ID.
- The customized Android host project is versioned. The current root
  `.gitignore` broadly ignores `apps/flutter_app_fastfood/android/`; remove that
  broad rule before release and commit the non-secret Android project files.
  Continue ignoring `android/key.properties`, `local.properties`, `.gradle/`,
  build output, and all keystores. Do not use `git add -f android`, because it
  can force-add secrets and machine-local files.
- The release decision states whether reward-product promotions (for example
  buy-X-get-Y/free-item rewards) are supported. If their cloud-to-POS contract
  is not complete, disable those promotion types for the release.
- Verify the supported POS build sends its active `session_id` on online and offline
  checkout and that Sales/Reports can filter the resulting invoices by shift. The
  backend keeps a compatibility fallback for legacy/manual clients that omit the
  field; new releases must not rely on it. Follow
  [`../apps/backend_fastfood/docs/SALES_AND_REPORTING.md`](../apps/backend_fastfood/docs/SALES_AND_REPORTING.md).
- One real Windows device, one real Android device, and the required printers
  pass the staging acceptance test. Automated tests do not validate Bluetooth,
  USB drivers, paper width, or physical print quality.

Current technical findings and historical security probes are recorded in
[`../AUDIT_HISTORY.md`](../AUDIT_HISTORY.md). Some tests in
`tests/audit_deployment_checks.py` intentionally try to reproduce old insecure
behavior; a rejected exploit may appear as a failed reproduction. Use the
normal `pytest -q` release gate as the authoritative suite result.

## 2. Workstation pre-deploy gate (Windows PowerShell)

### 2.1 Review and freeze the release

Run from the repository root:

```powershell
Set-Location D:\muti-saas
git status --short
git diff --stat
git diff
git ls-files apps/backend_fastfood/alembic/versions
git check-ignore -v apps/flutter_app_fastfood/android/app/build.gradle.kts
git ls-files apps/flutter_app_fastfood/android
```

Review every modified, deleted, and untracked file. In particular, confirm all
new migrations, POS services, receipt/printer code, and documentation are
tracked. The `check-ignore` command must eventually report no broad root rule
for `android/app/build.gradle.kts`, and `git ls-files .../android` must list the
non-secret Android project. Do not discard a dirty working tree merely to make
this check pass.

Remove only this broad line from the root `.gitignore`:

```gitignore
apps/flutter_app_fastfood/android/
```

Keep the Android folder's own `.gitignore` and the root signing-key rules. Then
run from `D:\muti-saas`, inspect the list, and stage the non-secret host project:

```powershell
Set-Location D:\muti-saas
git status --short -- apps/flutter_app_fastfood/android .gitignore
git add .gitignore apps/flutter_app_fastfood/android
git diff --cached --name-only
git ls-files | Select-String -Pattern 'key\.properties$|local\.properties$|\.jks$|\.keystore$|/\.gradle/'
```

The final command must print nothing. If it prints a secret or machine-local
file, unstage that exact file with `git restore --staged -- <path>` and correct
the ignore rules before continuing.

Check that secrets and generated artifacts are not tracked:

```powershell
Set-Location D:\muti-saas
git ls-files | Select-String -Pattern '(^|/)(\.env|key\.properties)$|\.jks$|\.keystore$|(^|/)media/|(^|/)build/'
git grep -n -I -E 'SECRET_KEY=.+|SMTP_PASSWORD=.+|PLATFORM_ADMIN_PASSWORD=.+' -- ':!*.example' ':!*.md'
```

Both commands should produce no real secret or generated-file match. A key
name in source code is normal; an assigned production value is not.

### 2.2 Backend and database checks

Run from `D:\muti-saas\apps\backend_fastfood`:

```powershell
Set-Location D:\muti-saas\apps\backend_fastfood
$env:ENVIRONMENT = 'development'
$env:DEBUG = 'false'
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m alembic heads
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m pytest -q
```

Required result: dependencies are consistent, exactly one Alembic head exists,
the local database reaches that head, and the complete suite passes. A local
upgrade does not replace a fresh-database migration rehearsal or a restore test
against a sanitized production-like backup.

### 2.3 Web dashboard checks

Run from `D:\muti-saas`. Setting `DEBUG=false` avoids inheriting an invalid
machine-level value such as `DEBUG=release`.

```powershell
Set-Location D:\muti-saas
$env:DEBUG = 'false'
python apps/web_fastfood/tests/local_css_smoke.py
python apps/web_fastfood/tests/platform_startup_smoke.py
python apps/web_fastfood/tests/tenant_startup_smoke.py
python apps/web_fastfood/tests/menu_tracking_ui_smoke.py
python apps/web_fastfood/tests/inventory_ui_smoke.py
python apps/web_fastfood/tests/sales_ui_smoke.py
python apps/web_fastfood/tests/expense_ui_smoke.py
python apps/web_fastfood/tests/payroll_ui_smoke.py
python apps/backend_fastfood/tests/browser_remediation_check.py
```

Then run the manual workflow in
[`../E2E_ACCEPTANCE_TEST.md`](../E2E_ACCEPTANCE_TEST.md) against a staging HTTPS
deployment. Static smoke tests do not replace browser and tenant-isolation tests.

### 2.4 Flutter checks

Run from `D:\muti-saas\apps\flutter_app_fastfood`:

```powershell
Set-Location D:\muti-saas\apps\flutter_app_fastfood
flutter doctor -v
flutter pub get
dart run build_runner build --delete-conflicting-outputs
flutter analyze
flutter test
```

Record the Flutter version and test output in the release evidence. Run
`build_runner` whenever annotated sync/database models changed and commit only
generated source that the repository intentionally tracks.

### 2.5 Commit, tag, and push

**First release only — no remote configured yet:** `git push origin main`
below assumes a GitHub remote already exists. If `git remote -v` prints
nothing, stop and follow
[`GIT-GITHUB-MAINTENANCE.md`](GIT-GITHUB-MAINTENANCE.md) §2.2-2.4 first
(create the GitHub repository, confirm the branch is `main`, add the
remote, push) — then continue here for the tag.

Run from `D:\muti-saas` only after the review and test gates pass:

```powershell
Set-Location D:\muti-saas
git add -A
git diff --cached --stat
git diff --cached
git commit -m "Prepare production release"
git push origin main
git tag -a v1.0.0 -m "Production v1.0.0"
git push origin v1.0.0
git status --short
git rev-parse HEAD
```

Use the project's real branch and version instead of the examples. The final
`git status --short` must be empty. Save the commit SHA with the release notes.

## 3. First production server setup (Ubuntu)

These commands run on the VPS, not on the Windows development machine. This section is
the complete first-server walkthrough; do not combine it with an older setup checklist.

### 3.1 Install operating-system packages

Run from any directory:

```bash
sudo apt update
sudo apt -y upgrade
sudo apt install -y python3.11 python3.11-venv python3.11-dev build-essential nginx postgresql postgresql-contrib libpq-dev git ufw certbot python3-certbot-nginx
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
```

The public firewall should not expose PostgreSQL or port 8000. nginx is the
only public entry point.

### 3.2 Create PostgreSQL role and database

Run from any directory. Use a generated password and safely URL-encode special
characters before placing it in `DATABASE_URL`.

```bash
sudo -u postgres psql
```

At the PostgreSQL prompt:

```sql
CREATE ROLE fastfood LOGIN PASSWORD 'CHANGE_ME_STRONG';
CREATE DATABASE fastfood OWNER fastfood;
\q
```

Verify Postgres is not reachable from outside the VPS rather than assuming Ubuntu's
package default holds — `listen_addresses` should be `localhost` and this should show
only loopback addresses:

```bash
sudo ss -tlnp | grep 5432
```

### 3.3 Clone the exact release and create the virtual environment

Run from any directory:

```bash
sudo mkdir -p /var/www
sudo chown "$USER":"$USER" /var/www
git clone YOUR_REPOSITORY /var/www/multi-saas
cd /var/www/multi-saas
git fetch --tags origin
git checkout v1.0.0
git rev-parse HEAD
cd /var/www/multi-saas/apps/backend_fastfood
python3.11 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
```

Deploying a release tag makes the deployed source reproducible. If policy uses
`main`, record the exact commit SHA instead.

### 3.4 Create the production environment file

Run from `/var/www/multi-saas/apps/backend_fastfood`:

```bash
cd /var/www/multi-saas/apps/backend_fastfood
cp .env.example .env
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
nano .env
```

Required production values:

```dotenv
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql+psycopg://fastfood:CHANGE_ME@localhost:5432/fastfood
SECRET_KEY=PASTE_ONE_STABLE_RANDOM_VALUE
CORS_ORIGINS=https://YOUR.DOMAIN
PLATFORM_ADMIN_EMAIL=YOUR_EMAIL
PLATFORM_ADMIN_PASSWORD=CHANGE_ME_STRONG_TEMPORARY_PASSWORD
SMTP_HOST=YOUR_SMTP_HOST
SMTP_PORT=587
SMTP_USERNAME=YOUR_SMTP_USERNAME
SMTP_PASSWORD=YOUR_SMTP_PASSWORD
SMTP_FROM_EMAIL=YOUR_VERIFIED_SENDER
SMTP_FROM_NAME=Storixx
```

Keep `SECRET_KEY` stable: rotating it invalidates web and POS tokens. Do not use
`CORS_ORIGINS=*` in production. SMTP setup and test procedures are in
[`EMAIL-SETUP.md`](EMAIL-SETUP.md).

Create writable media storage:

```bash
cd /var/www/multi-saas/apps/backend_fastfood
mkdir -p media
sudo chown -R www-data:www-data media
```

### 3.5 Migrate and bootstrap

Run from `/var/www/multi-saas/apps/backend_fastfood`:

```bash
cd /var/www/multi-saas/apps/backend_fastfood
.venv/bin/python -m alembic heads
.venv/bin/python -m alembic current
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m alembic current
.venv/bin/python scripts/bootstrap_platform.py
sudo chown www-data:www-data .env
sudo chmod 600 .env
sudo -u www-data .venv/bin/python -c "from core.config import settings; print(settings.ENVIRONMENT, settings.DEBUG, settings.CORS_ORIGINS)"
```

`heads` must show one head and the final `current` must equal it. Never hardcode
a migration revision in deployment commands. The final configuration check must
print `production False` and the exact HTTPS origin without printing any secret.
The `.env` ownership is changed only after migration/bootstrap so those commands
can read it as the deployment user; the service then reads it as `www-data`.

`deploy/fastapi.service` also runs `scripts/prepare_database.py` (migrate +
bootstrap, idempotent) as `ExecStartPre` on **every** start and restart of the
`multi-saas` unit — so the manual run above is a pre-flight check, not the only
place migrations happen. Two consequences: a failed migration blocks the
service from starting at all (a safety net, not a bug), and the `www-data` user
itself — not just the deploy user running this section — must have the
PostgreSQL privileges to run migrations, since `ExecStartPre` runs as `www-data`
per the unit's `User=` directive.

### 3.6 Install systemd, nginx, DNS, and TLS

First create the DNS `A` record (and `AAAA` only if IPv6 is configured) for
`YOUR.DOMAIN`. Wait until it resolves to the VPS.

Run from `/var/www/multi-saas`:

```bash
cd /var/www/multi-saas
sudo cp deploy/fastapi.service /etc/systemd/system/multi-saas.service
sudo systemctl daemon-reload
sudo systemctl enable --now multi-saas
sudo systemctl status multi-saas --no-pager
curl -fsS http://127.0.0.1:8000/health

# nginx (www-data) needs execute rights up the tree to read/traverse into the
# checkout — a stricter-than-default umask on clone otherwise causes 403s:
sudo chmod o+X /var/www /var/www/multi-saas /var/www/multi-saas/apps

sudo cp deploy/nginx.conf /etc/nginx/sites-available/multi-saas
sudo sed -i 's/app.example.com/YOUR.DOMAIN/g' /etc/nginx/sites-available/multi-saas
sudo ln -sfn /etc/nginx/sites-available/multi-saas /etc/nginx/sites-enabled/multi-saas
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d YOUR.DOMAIN --redirect --agree-tos -m YOUR_EMAIL
sudo certbot renew --dry-run
```

If repository service/nginx paths differ from the actual checkout, edit and
review them before copying. After Certbot modifies the live nginx file, do not
blindly overwrite it with the HTTP template during later releases.

### 3.7 Optional: a staging environment first

Recommended before the first production release, and before any release that
touches a migration, a payment flow, or POS sync. Staging is not a separate
procedure — it is section 3 run again with different names, on either a
second small VPS or a second nginx server block + Postgres database on the
same box:

- DNS/domain: a subdomain, e.g. `staging.YOUR.DOMAIN`, its own `A` record.
- Checkout path: e.g. `/var/www/multi-saas-staging` instead of
  `/var/www/multi-saas`.
- Database: a separate role/database, e.g. `fastfood_staging`, never the
  production `fastfood` database.
- systemd unit / nginx site name: e.g. `multi-saas-staging`, so
  `systemctl`/`journalctl`/nginx commands never collide with production.
- `.env`: its own `SECRET_KEY` (never reused from production —
  rotating either one independently must not affect the other) and its own
  `CORS_ORIGINS=https://staging.YOUR.DOMAIN`.

Run the full `E2E_ACCEPTANCE_TEST.md` script against staging (section 5.2
below covers the same list) before repeating section 3 for production, and
again after every later release before it reaches production (section 7).
A staging pilot is what "the staging API contract has passed" in section 4
below refers to.

## 4. Build production POS clients (Windows workstation)

Build only after `https://YOUR.DOMAIN/health` works and the staging API contract
has passed. `API_URL` is compiled into each client; changing it requires a new
build and installation.

Use the full signing and printer instructions in
[`../apps/flutter_app_fastfood/BUILD_CLIENTS.md`](../apps/flutter_app_fastfood/BUILD_CLIENTS.md).

### 4.1 Windows release and installer

Run from `D:\muti-saas\apps\flutter_app_fastfood`:

```powershell
Set-Location D:\muti-saas\apps\flutter_app_fastfood
flutter clean
flutter pub get
flutter build windows --release --dart-define=API_URL=https://YOUR.DOMAIN
& "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" installer\smart_shop.iss
```

Outputs:

- Flutter directory: `build\windows\x64\runner\Release\`
- Installer: `installer\dist\SmartShop-Setup-<version>.exe`

Keep `pubspec.yaml` and `installer/smart_shop.iss` versions aligned. Sign the
installer/executable with the organization's code-signing certificate when one
is available. Test the installer on a clean Windows account before release.

### 4.2 Android signing and release

Before the first public Android release, set the permanent `namespace` and
`applicationId` in `android/app/build.gradle.kts`.

Create the keystore once and store it in a backed-up secrets location outside
Git. Run from the directory in which that protected key should be created:

```powershell
keytool -genkeypair -v -keystore smart-shop-upload.jks -keyalg RSA -keysize 2048 -validity 10000 -alias upload
```

Create `D:\muti-saas\apps\flutter_app_fastfood\android\key.properties`:

```properties
storePassword=CHANGE_ME
keyPassword=CHANGE_ME
keyAlias=upload
storeFile=C:/secure/path/smart-shop-upload.jks
```

Then run from `D:\muti-saas\apps\flutter_app_fastfood`:

```powershell
Set-Location D:\muti-saas\apps\flutter_app_fastfood
flutter clean
flutter pub get
flutter build appbundle --release --dart-define=API_URL=https://YOUR.DOMAIN
flutter build apk --release --dart-define=API_URL=https://YOUR.DOMAIN
```

Outputs are under `build\app\outputs\bundle\release\` and
`build\app\outputs\flutter-apk\`. Never commit or lose the keystore,
passwords, or `key.properties`.

### 4.3 Artifact record

Run from `D:\muti-saas` and save the hashes with the release notes:

```powershell
Set-Location D:\muti-saas
Get-FileHash apps\flutter_app_fastfood\installer\dist\SmartShop-Setup-*.exe -Algorithm SHA256
Get-FileHash apps\flutter_app_fastfood\build\app\outputs\flutter-apk\*-release.apk -Algorithm SHA256
Get-FileHash apps\flutter_app_fastfood\build\app\outputs\bundle\release\*.aab -Algorithm SHA256
```

## 5. Post-deployment verification

### 5.1 Server checks

Run on the VPS from any directory:

```bash
curl -fsS https://YOUR.DOMAIN/health
curl -fsS http://127.0.0.1:8000/ready
curl -I https://YOUR.DOMAIN/platform/login.html
curl -I https://YOUR.DOMAIN/tenant/login.html
sudo systemctl is-active multi-saas nginx postgresql
sudo journalctl -u multi-saas --since '15 minutes ago' --no-pager
sudo tail -n 100 /var/log/nginx/error.log
```

Expected: health/readiness succeed, both login pages return a successful or
redirect response, services are active, and logs contain no repeating errors.

### 5.2 Functional acceptance

Use two tenants, two branches, and test-only users/data:

1. Log into the platform dashboard, then each tenant dashboard.
2. Confirm tenant and branch isolation; Tenant A must never see Tenant B data.
3. Create/update a tracked product and color variant, stock, tax, and permitted
   promotion. Confirm inventory totals and low-stock filtering/notification.
4. Generate a device activation code and activate one Windows and one Android
   POS. Confirm shop, branch, logo, receipt fields, and catalog sync.
5. Open a cashier shift. Complete cash and each enabled electronic payment.
6. Verify sale, payment breakup, stock deduction, receipt number, dashboard
   report, and branch report agree.
7. Test discount, refund, stock restoration, and shift closing totals.
8. Disconnect one client, create an allowed offline sale, reconnect, sync, and
   confirm it uploads exactly once.
9. Print and save both A4 and 80 mm receipts. Test Windows system printing and
   the actual Android/Windows Bluetooth workflow required by the business.
10. Test password-reset email delivery and check spam/domain authentication.

The detailed script is [`../E2E_ACCEPTANCE_TEST.md`](../E2E_ACCEPTANCE_TEST.md).
Do not release all clients until a small pilot installation passes this list.

## 6. Backups, monitoring, and routine operation

### 6.1 Create a backup before every release

Run on the VPS. The backup directory must exist on a protected disk and copies
must also leave the VPS.

```bash
sudo install -d -m 700 -o postgres -g postgres /var/backups/multi-saas
sudo -u postgres pg_dump -Fc fastfood -f /var/backups/multi-saas/fastfood-before-release.dump
sudo tar -C /var/www/multi-saas/apps/backend_fastfood -czf /var/backups/multi-saas/media-before-release.tar.gz media
sudo -u postgres pg_restore --list /var/backups/multi-saas/fastfood-before-release.dump >/dev/null
```

An archive listing is only a basic integrity check. Periodically restore into a
separate disposable database and run health/data checks. Encrypt and copy both
database and media backups off-site; define retention and test recovery.

This pre-release backup is a one-off, manual step — it does not replace a recurring
schedule. Install one on first setup, not just before releases:

```bash
echo '0 2 * * * postgres pg_dump -Fc fastfood -f /var/backups/multi-saas/fastfood-$(date +\%F).dump' \
  | sudo tee /etc/cron.d/multi-saas-backup
sudo find /var/backups/multi-saas -name 'fastfood-*.dump' -mtime +14 -delete   # example retention; adjust as needed
```

Rotate/delete old dumps on a schedule that matches your retention policy, and confirm the
off-box copy (rsync, object storage, etc.) runs on the same cadence — a local-only backup on
the same VPS does not survive a lost disk or a compromised host.

### 6.2 Monitoring commands

Run on the VPS from any directory:

```bash
sudo systemctl status multi-saas nginx postgresql --no-pager
sudo journalctl -u multi-saas -f
sudo tail -f /var/log/nginx/error.log
sudo nginx -t
sudo certbot certificates
df -h
```

Configure an external monitor for `https://YOUR.DOMAIN/health`, alerting for
service failures, repeated HTTP 5xx responses, low disk space, failed backups,
certificate expiry, and PostgreSQL capacity. Application logs must not contain
passwords, tokens, card data, or SMTP secrets.

## 7. Deploying a later release

Deploy a reviewed tag or exact commit. Take backups first. Run on the VPS:

```bash
cd /var/www/multi-saas
git status --short
git fetch --tags origin
git checkout v1.0.1
git rev-parse HEAD

cd /var/www/multi-saas/apps/backend_fastfood
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
.venv/bin/python -m alembic heads
.venv/bin/python -m alembic current
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m alembic current
sudo systemctl restart multi-saas
sudo systemctl status multi-saas --no-pager
curl -fsS http://127.0.0.1:8000/health
curl -fsS https://YOUR.DOMAIN/health
```

If nginx or systemd templates changed, merge reviewed changes into the live
files, preserving the real domain and Certbot TLS blocks. Validate nginx before
reload; run `systemctl daemon-reload` after changing the unit.

Dashboard HTML/JS/CSS is served from the checkout and needs no backend restart,
but users may need a hard refresh. Rebuild POS clients only when their code,
embedded API URL, or API/sync contract changes. Deploy a backward-compatible
backend before distributing new clients wherever possible.

## 8. Rollback and recovery

### Code-only rollback

Use this only when no incompatible migration or new-version data write occurred:

```bash
cd /var/www/multi-saas
git checkout PREVIOUS_TESTED_TAG
cd apps/backend_fastfood
.venv/bin/python -m pip install -r requirements.txt
sudo systemctl restart multi-saas
curl -fsS https://YOUR.DOMAIN/health
```

### Migration or data rollback

Do not run `alembic downgrade -1` blindly. A downgrade may delete columns or
data and old code may not understand rows written by the new release. Stop the
rollout, preserve logs and affected POS outboxes, review the migration's
`downgrade()` and release notes, and choose either:

- a tested forward-fix migration; or
- a maintenance window that restores the verified pre-release database and
  matching media backup, then checks out the matching code tag.

Example restore into an empty recovery database, run from the VPS:

```bash
sudo -u postgres createdb fastfood_recovery
sudo -u postgres pg_restore --clean --if-exists --no-owner --dbname=fastfood_recovery /var/backups/multi-saas/fastfood-before-release.dump
sudo -u postgres psql -d fastfood_recovery -c 'SELECT current_database(), now();'
```

Validate the recovery database before replacing production. Preserve pending
offline sales on every POS; never delete an outbox merely to clear an error.

## 9. Release evidence to retain

For every release, retain:

- version/tag and Git commit SHA;
- Alembic revision before and after deployment;
- test results and staging acceptance sign-off;
- dependency/runtime versions;
- backup filenames and restore-test result;
- production URL and client `API_URL` used at build time;
- installer/APK/AAB SHA-256 hashes and signing identity;
- deployment time, operator, smoke-test result, and any incident/rollback.

## 10. Related documentation

- [`GIT-GITHUB-MAINTENANCE.md`](GIT-GITHUB-MAINTENANCE.md): commits, GitHub, versioning, tags, releases, and repository maintenance
- [`CHANGE-OWNERSHIP.md`](CHANGE-OWNERSHIP.md): files and compatibility checks affected by each change type
- [`EMAIL-SETUP.md`](EMAIL-SETUP.md): SMTP and password-reset delivery
- [`../DOCUMENTATION.md`](../DOCUMENTATION.md): source-of-truth map for all maintained documentation
- [`../apps/flutter_app_fastfood/BUILD_CLIENTS.md`](../apps/flutter_app_fastfood/BUILD_CLIENTS.md): POS build, signing, and printing
- [`../E2E_ACCEPTANCE_TEST.md`](../E2E_ACCEPTANCE_TEST.md): manual acceptance test
- [`../AUDIT_HISTORY.md`](../AUDIT_HISTORY.md): dated findings and verification history
