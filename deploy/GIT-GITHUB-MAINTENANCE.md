# Git, GitHub, versioning, and release maintenance

This guide explains how to preserve the project in Git, connect it to GitHub,
make later changes safely, publish releases, and keep deployed environments
traceable. It complements the production commands in
[`DEPLOYMENT-RUNBOOK.md`](DEPLOYMENT-RUNBOOK.md).

All Windows commands use PowerShell and assume the repository is located at
`D:\muti-saas`. Server commands use Ubuntu and assume the deployment is located
at `/var/www/multi-saas`.

## 1. Repository state and terminology

At the time this guide was added:

- the local branch is `main` (renamed from `master` per §2.3 below);
- no GitHub remote is configured;
- no release tags exist;
- commit `d2fd6c3` ("Initial commit") is the current baseline — the full
  prior history (previously anchored at `4a4a24f`) was squashed into this
  single commit ahead of first deployment. A full bundle backup of the
  pre-squash history was kept outside the repository; ask the person who ran
  the squash if you need to look something up in it.

These facts will change. Always inspect the live state instead of relying on
the list above:

```powershell
Set-Location D:\muti-saas
git status
git branch -vv
git remote -v
git tag --list --sort=-version:refname
git log -5 --oneline --decorate
```

Important terms:

- **working tree**: files currently on disk;
- **staging area/index**: the exact changes prepared for the next commit;
- **commit**: an immutable snapshot with author, date, parent, and message;
- **branch**: a movable name pointing to a line of commits;
- **remote**: another Git repository, normally GitHub;
- **tag**: a fixed name for an exact release commit;
- **pull request (PR)**: GitHub review and merge workflow;
- **release artifact**: installer, APK, AAB, checksum, or release notes built
  from a tagged commit.

## 2. One-time Git identity and GitHub setup

### 2.1 Configure the commit author

Prefer repository-local identity when this computer is shared. Run from
`D:\muti-saas`:

```powershell
Set-Location D:\muti-saas
git config user.name "YOUR NAME"
git config user.email "YOUR VERIFIED GITHUB EMAIL"
git config --get user.name
git config --get user.email
```

GitHub attributes commits to an account when the commit email matches a
verified account email. A GitHub-provided private `noreply` email is also valid.

### 2.2 Create the GitHub repository

On GitHub, create an empty private repository unless this source is intended to
be public. Do not initialize it with a README, license, or `.gitignore` when the
local repository already contains history.

Enable two-factor authentication for maintainers. Grant write/admin access only
to people who need it. Never send account passwords, personal access tokens,
SSH private keys, production `.env` files, database backups, or signing
keystores through GitHub issues or chat.

### 2.3 Choose the permanent default branch

**Already done for this repository** — the local branch was renamed to
`main` ahead of the first push. The steps below are kept for reference (a
fresh clone elsewhere, or a future project) and to explain why `main` is
what the rest of this guide uses.

Either keep the branch named `master` everywhere, or rename it once to
`main` before the first push. The commands in the rest of this guide use
`main`.

To rename before the first remote push, run from `D:\muti-saas`:

```powershell
Set-Location D:\muti-saas
git branch -M main
git branch --show-current
```

Do not repeatedly rename a branch after deployments and automation already use
it. If GitHub already contains a default branch, coordinate the rename in
GitHub settings and update server/CI references.

### 2.4 Connect and push with HTTPS

Replace `OWNER` and `REPOSITORY`:

```powershell
Set-Location D:\muti-saas
git remote add origin https://github.com/OWNER/REPOSITORY.git
git remote -v
git push -u origin main
```

Use Git Credential Manager, GitHub CLI login, or a fine-grained personal access
token when prompted. Do not put a token inside the remote URL.

If `origin` already exists, verify it before changing it:

```powershell
git remote get-url origin
git remote set-url origin https://github.com/OWNER/REPOSITORY.git
```

### 2.5 Connect with SSH instead

Add the public SSH key to GitHub, protect the private key, then use:

```powershell
Set-Location D:\muti-saas
git remote add origin git@github.com:OWNER/REPOSITORY.git
ssh -T git@github.com
git push -u origin main
```

Use either HTTPS or SSH consistently. Both provide the same Git history.

## 3. Before every commit

Start from `D:\muti-saas`:

```powershell
Set-Location D:\muti-saas
git status --short
git diff --stat
git diff
```

Confirm that every modification, deletion, and new file is intended. Generated
source used by the application may belong in Git; runtime output, caches,
secrets, databases, and compiled installers do not.

Run the checks appropriate to the change. The complete release gate is in
[`DEPLOYMENT-RUNBOOK.md`](DEPLOYMENT-RUNBOOK.md#2-workstation-pre-deploy-gate-windows-powershell).

Backend, from `D:\muti-saas\apps\backend_fastfood`:

```powershell
Set-Location D:\muti-saas\apps\backend_fastfood
$env:DEBUG = 'false'
.\.venv\Scripts\python.exe -m alembic heads
.\.venv\Scripts\python.exe -m pytest -q
```

Flutter, from `D:\muti-saas\apps\flutter_app_fastfood`:

```powershell
Set-Location D:\muti-saas\apps\flutter_app_fastfood
flutter analyze
flutter test
```

Web smoke tests, from `D:\muti-saas`:

```powershell
Set-Location D:\muti-saas
$env:DEBUG = 'false'
python apps/web_fastfood/tests/local_css_smoke.py
python apps/web_fastfood/tests/platform_startup_smoke.py
python apps/web_fastfood/tests/tenant_startup_smoke.py
python apps/web_fastfood/tests/inventory_ui_smoke.py
python apps/web_fastfood/tests/menu_tracking_ui_smoke.py
python apps/web_fastfood/tests/sales_ui_smoke.py
```

## 4. Staging and committing changes

### 4.1 Preferred: stage related files explicitly

For a focused change, stage only its files:

```powershell
Set-Location D:\muti-saas
git add apps/backend_fastfood/schemas/sale.py
git add apps/web_fastfood/tenant/sales.html
git add apps/backend_fastfood/tests/test_pos_tenant_roundtrip.py
git diff --cached --stat
git diff --cached
git commit -m "Show cashier identity on synchronized sales"
```

This keeps unrelated work out of the commit.

### 4.2 Commit every intended change

Use this only when everything in the working tree belongs to one release:

```powershell
Set-Location D:\muti-saas
git status --short
git add -A
git diff --cached --stat
git diff --cached
git diff --cached --check
git commit -m "Describe the complete change"
```

`git add -A` includes additions, modifications, and deletions. Review the staged
diff before committing; staging is not proof that the files are safe.

### 4.3 Safe secret and artifact checks

After staging, run:

```powershell
Set-Location D:\muti-saas
git diff --cached --name-only | Select-String -Pattern '(^|/)(\.env|key\.properties|local\.properties)$|\.jks$|\.keystore$|(^|/)media/|(^|/)build/|(^|/)\.gradle/'
git grep --cached -n -I -E 'BEGIN [A-Z ]*PRIVATE KEY|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{20,}|xsmtpsib-[A-Za-z0-9_-]{12,}' -- .
```

Both commands should print nothing. `.env.example` and
`android/key.properties.example` may be committed only with obvious placeholder
values.

If an unwanted file is staged, keep the working file and remove only its staged
copy:

```powershell
git restore --staged -- path\to\file
```

Then add a precise ignore rule to `.gitignore` when appropriate.

### 4.4 Commit-message convention

Use an imperative summary no longer than about 72 characters. Explain why in a
body when the change is consequential.

Examples:

```text
Fix original cashier attribution for offline sales
Add 80 mm receipt printing and printer settings
Consolidate variant inventory routes
Document production backup and rollback procedure
```

For a larger commit:

```powershell
git commit -m "Improve POS sale synchronization" -m "Preserve the original cashier, expose human sale numbers, and add tenant-dashboard regression coverage."
```

Avoid messages such as `changes`, `fix`, `work`, or `updated files`.

### 4.5 Amend only an unpublished commit

If the latest commit has not been pushed/shared:

```powershell
git add path\to\forgotten-file
git commit --amend --no-edit
```

Do not amend or rebase commits already used by another developer or deployed
server unless everyone coordinates the history rewrite.

## 5. Daily branch and pull-request workflow

### 5.1 Start a feature or fix

```powershell
Set-Location D:\muti-saas
git status --short
git switch main
git fetch origin
git pull --ff-only origin main
git switch -c feature/short-description
```

Use names such as:

- `feature/receipt-branding`
- `fix/offline-cashier-attribution`
- `docs/deployment-maintenance`
- `hotfix/payment-rounding`

Commit logical checkpoints on the branch. Push it:

```powershell
git push -u origin feature/short-description
```

### 5.2 Open and review a pull request

On GitHub, open a PR from the feature branch into `main`. Include:

- problem and intended behavior;
- backend/web/POS/database areas changed;
- migration and compatibility impact;
- tests run and results;
- screenshots for UI changes;
- deployment, client rebuild, and rollback notes;
- known limitations.

With GitHub CLI, after `gh auth login`:

```powershell
gh pr create --base main --fill
gh pr checks
```

Merge only after review and required checks pass. Prefer a normal merge or
squash merge according to one consistent repository policy. Delete merged
feature branches; never delete release tags.

### 5.3 Refresh a feature branch

For a shared branch, merging `main` avoids rewriting shared history:

```powershell
git fetch origin
git switch feature/short-description
git merge origin/main
```

Resolve conflicts deliberately, run tests again, commit the merge if needed,
and push. Rebase only private/unpublished work or with explicit coordination.

### 5.4 Update local `main` after merge

```powershell
git switch main
git pull --ff-only origin main
git branch -d feature/short-description
git status
```

`--ff-only` prevents an accidental local merge commit on the deployment branch.

## 6. GitHub repository protection

Configure the GitHub default branch and a branch ruleset for `main`:

- require pull requests before merging;
- require at least one approval when multiple maintainers exist;
- dismiss stale approvals after new commits;
- require resolved conversations;
- require automated checks once CI is configured;
- block force pushes and branch deletion;
- restrict bypass permission;
- enable secret scanning, push protection, and dependency alerts when available;
- require two-factor authentication for the organization/team.

This repository does not currently contain a `.github/workflows` CI pipeline.
Do not mark a non-existent check as required. When CI is added, run the same
backend, Flutter, and web gates documented above and protect `main` with those
check names.

Use GitHub environments for staging/production deployment secrets. Secrets must
be environment/repository secrets, never values committed to workflow YAML.

## 7. Version numbering

Use Semantic Versioning: `MAJOR.MINOR.PATCH`.

- **MAJOR**: incompatible API, sync, database, or operational contract change;
- **MINOR**: backward-compatible feature;
- **PATCH**: backward-compatible bug/security fix.

Examples: `1.0.0`, `1.1.0`, `1.1.1`, `2.0.0`.

Version surfaces in this repository:

| Surface | File | Example |
|---|---|---|
| Flutter version and Android build number | `apps/flutter_app_fastfood/pubspec.yaml` | `version: 1.2.0+15` |
| Windows installer version | `apps/flutter_app_fastfood/installer/smart_shop.iss` | `#define AppVersion "1.2.0"` |
| Backend/API display version | `apps/backend_fastfood/app/main.py` | `version="1.2.0"` |
| Git release tag | repository tag | `v1.2.0` |

The Android build number after `+` must increase for every store upload, even
when the visible version is unchanged. Keep the Flutter visible version,
Windows installer version, backend version when applicable, tag, and release
notes aligned.

Do not increase a database or POS sync protocol version just because the
marketing version changed. Change a protocol version only when its serialized
contract is incompatible, and update server/client compatibility tests together.

## 8. Database migration version control

Every schema or durable data change requires a new Alembic migration committed
with its model/service/test changes. Never edit a migration already applied in
production; add another migration.

Create and inspect a migration from
`D:\muti-saas\apps\backend_fastfood`:

```powershell
Set-Location D:\muti-saas\apps\backend_fastfood
.\.venv\Scripts\python.exe -m alembic revision -m "describe change"
.\.venv\Scripts\python.exe -m alembic heads
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current
```

Autogenerated or empty migrations must be reviewed manually for constraints,
defaults, data conversions, downgrade safety, table locks, and tenant/branch
integrity. Required release rules:

- exactly one Alembic head;
- migration file is tracked and included in the release tag;
- upgrade tested on an empty database and representative existing data;
- database backup and restore procedure tested;
- backend deployed in a client-compatible order;
- destructive downgrade is never automatic.

## 9. Preparing a release

### 9.1 Create a release branch when stabilization is needed

For a small project, a tested `main` commit may be tagged directly. For a
stabilization period:

```powershell
Set-Location D:\muti-saas
git switch main
git pull --ff-only origin main
git switch -c release/1.2.0
```

Allow only version, documentation, and release-blocking fixes on this branch.
Merge final fixes back into `main` so histories do not diverge.

### 9.2 Run the release gate

Follow [`DEPLOYMENT-RUNBOOK.md`](DEPLOYMENT-RUNBOOK.md) completely. At minimum:

- working tree clean;
- staged/committed secrets absent;
- one Alembic head and migration rehearsal passed;
- full backend, Flutter, and web suites passed;
- staging HTTPS acceptance completed;
- Windows and Android clients tested against the production-compatible API;
- database/media backups and restore evidence available;
- Android signing identity and artifact checksums recorded.

### 9.3 Create an annotated release tag

Tag the exact tested commit, not an uncommitted working tree:

```powershell
Set-Location D:\muti-saas
git status --short
git log -1 --oneline
git tag -a v1.2.0 -m "Production release 1.2.0"
git show v1.2.0 --no-patch
git push origin v1.2.0
```

Do not move or reuse a published release tag. If a release is wrong, create a
new patch version such as `v1.2.1`.

### 9.4 Create the GitHub release

Attach only distributable artifacts:

- signed Windows installer;
- signed Android APK for controlled sideloading when required;
- signed AAB for store submission;
- SHA-256 checksum file;
- release notes and upgrade/rollback requirements.

Do not attach source `.env`, keystores, database/media backups, raw local POS
databases, or debug builds.

With GitHub CLI:

```powershell
gh release create v1.2.0 --title "Storixx 1.2.0" --notes-file RELEASE-NOTES.md `
  apps\flutter_app_fastfood\installer\dist\SmartShop-Setup-1.2.0.exe `
  apps\flutter_app_fastfood\build\app\outputs\flutter-apk\smart-shop-release.apk
```

Use only paths that exist for that release. An AAB is normally uploaded to the
store console rather than distributed to users directly.

## 10. Deploying a tagged version

The production server should deploy a reviewed tag or recorded commit, not an
unknown working tree. Follow the backup and migration order in the deployment
runbook.

On the Ubuntu VPS:

```bash
cd /var/www/multi-saas
git status --short
git fetch --tags origin
git checkout v1.2.0
git rev-parse HEAD
```

Then continue with dependencies, migrations, service restart, and smoke tests
in [`DEPLOYMENT-RUNBOOK.md`](DEPLOYMENT-RUNBOOK.md#7-deploying-a-later-release).

Record production environment state:

```bash
cd /var/www/multi-saas
git describe --tags --always --dirty
git rev-parse HEAD
cd apps/backend_fastfood
.venv/bin/python -m alembic current
```

`--dirty` must not appear on a managed production checkout. Production `.env`,
media, logs, backups, and runtime data remain outside Git.

## 11. Hotfix workflow

For an urgent production fix, branch from the deployed tag:

```powershell
Set-Location D:\muti-saas
git fetch --tags origin
git switch -c hotfix/1.2.1 v1.2.0
```

Make the smallest safe fix, add regression tests, run the release gate, commit,
and push:

```powershell
git add path\to\changed-files
git diff --cached
git commit -m "Fix production issue description"
git push -u origin hotfix/1.2.1
```

Open a PR into `main`, merge it, tag the merged tested commit as `v1.2.1`, and
deploy that tag. If a long-lived release branch exists, merge/cherry-pick the
fix there through review as well. Never leave a production-only fix absent from
`main`.

## 12. Undoing changes safely

### Uncommitted file

Inspect before discarding:

```powershell
git diff -- path\to\file
git restore -- path\to\file
```

`git restore` discards local work. Use it only for an exact reviewed path.

### Staged but not committed

Keep the file change but unstage it:

```powershell
git restore --staged -- path\to\file
```

### Published commit

Create a new commit that reverses it:

```powershell
git switch main
git pull --ff-only origin main
git revert COMMIT_SHA
git push origin main
```

`git revert` preserves shared history. Do not use `git reset --hard` or force
push on shared/deployed history.

### Failed deployment

A Git revert does not automatically undo database writes, migrations, media,
queued offline sales, or client installations. Follow
[`DEPLOYMENT-RUNBOOK.md`](DEPLOYMENT-RUNBOOK.md#8-rollback-and-recovery). Prefer a
forward fix after a data migration; restore a verified pre-release backup only
under a controlled recovery plan.

## 13. Secret exposure procedure

If a secret is committed:

1. Immediately revoke/rotate the credential. Removing it from Git does not make
   the exposed credential safe.
2. Remove it from current files and add the appropriate ignore rule.
3. Determine whether rewriting history is required by organizational policy.
4. If rewriting, use a reviewed history-cleaning tool such as `git filter-repo`,
   coordinate with every clone and deployed server, force-push only the affected
   refs, and invalidate old clones.
5. Re-run secret scanning and record the incident.

Never paste the exposed value into an issue, commit message, PR, or command log.

## 14. Repository maintenance schedule

### Every change

- use a focused branch and regression tests;
- review working and staged diffs;
- check secrets and generated artifacts;
- keep migrations, server contract, clients, tests, and docs synchronized;
- push the branch and use a PR once GitHub collaboration begins.

### Every release

- update versions and release notes;
- run the full release/staging gates;
- take and verify backups;
- tag the exact tested commit;
- retain artifact hashes and previous signed installers;
- deploy the tag and record Git/Alembic revisions;
- monitor logs, synchronization, payments, shifts, inventory, and reports.

### Monthly

- review dependency/security alerts and update in tested batches;
- verify branch protection, collaborator access, and inactive credentials;
- verify off-site database/media backups and certificate expiry;
- prune merged remote branches through GitHub policy;
- inspect disk use, logs, and repository size.

### Quarterly or before a major release

- perform a real backup restore rehearsal;
- test a clean clone and fresh environment build;
- test Windows/Android upgrades without losing POS activation or offline outbox;
- review tenant isolation and branch-report integrity;
- review Android upload-key and Windows signing-certificate recovery access;
- remove obsolete deployment access and rotate credentials according to policy.

## 15. Useful inspection and recovery commands

Run from `D:\muti-saas` unless stated otherwise:

```powershell
# Concise state
git status --short --branch

# History including branches and tags
git log --graph --decorate --oneline --all -30

# What changed in one commit
git show --stat COMMIT_SHA
git show COMMIT_SHA -- path\to\file

# Compare local branch with GitHub
git fetch origin
git log --oneline HEAD..origin/main
git log --oneline origin/main..HEAD

# Find which commit changed a line/file
git log --follow -- path\to\file
git blame path\to\file

# Find branches already merged into main
git branch --merged main

# Confirm a tag points to the expected commit
git show v1.2.0 --no-patch --decorate

# Verify repository object integrity
git fsck --full
```

Avoid routine use of destructive cleanup commands. Never run a broad reset,
clean, or recursive deletion merely to make `git status` empty.

## 16. Release record template

Copy this into the GitHub release notes or an internal release record:

```text
Release: vX.Y.Z
Date/time/timezone:
Operator/reviewer:
Git commit SHA:
Previous production tag/SHA:
Alembic before/after:
Backend version:
Flutter version/build number:
Windows installer version:
Production API URL embedded in clients:
Backend tests:
Flutter analyze/tests:
Web smoke tests:
Staging acceptance:
Database backup:
Media backup:
Restore verification:
Windows installer SHA-256:
Android APK/AAB SHA-256:
Signing identity:
Deployment result:
Post-deploy smoke result:
Known limitations:
Rollback/forward-fix plan:
```

## 17. Related documentation

- [`DEPLOYMENT-RUNBOOK.md`](DEPLOYMENT-RUNBOOK.md): canonical deployment order
- [`CHANGE-OWNERSHIP.md`](CHANGE-OWNERSHIP.md): cross-application change map and compatibility rules
- [`../E2E_ACCEPTANCE_TEST.md`](../E2E_ACCEPTANCE_TEST.md): acceptance workflow
- [`../apps/flutter_app_fastfood/BUILD_CLIENTS.md`](../apps/flutter_app_fastfood/BUILD_CLIENTS.md): client build/signing details
