# Security, isolation, and readiness audit history — refreshed 13 September 2026

> This file is historical audit evidence, not an operational deployment guide. Migration
> revision IDs and open findings reflect the date of each audit pass and may be stale.
> Always re-run the gates and use the commands in
> [`deploy/DEPLOYMENT-RUNBOOK.md`](deploy/DEPLOYMENT-RUNBOOK.md).

## 24 September 2026 — migration and git history squashed ahead of first deployment

Not an audit pass; a housekeeping record. Ahead of the first production
deployment, the full Alembic migration chain (27 migrations, the last of
which was `c3d4e5f6a7b8`) was squashed into one fresh migration,
`2757039146da_initial_schema` (`down_revision = None`), verified by applying
it to an empty database, running `scripts/bootstrap_platform.py`, and a full
`pytest -q` pass (694/694) — twice, once against an isolated throwaway
schema and once against the real local dev database after re-stamping it to
the new head. Separately, the full git history (27 commits) was squashed
into one commit, `d2fd6c3` ("Initial commit"); a `git bundle` backup of the
pre-squash history was kept outside the repository. Neither change altered
application behavior or the database schema — see `LOCAL TESTING GUIDE.md`'s
migration checkpoint and `deploy/GIT-GITHUB-MAINTENANCE.md` §1 for the
current, authoritative state. As with the row below from 13 September, treat
any migration ID or commit hash in this file as a point-in-time record, not
a current reference — always get the real state with `alembic heads` /
`git log`.

**This is a re-audit of the 5 September 2026 baseline below, run after the Business/Variant/
Add-on model refactor (`COMPLETE-IMPLEMENTATION-SPEC.md` Parts A–J) and the Flutter POS
refactor that followed it.** Of the 24 findings from that baseline, **20 were re-probed this
pass and no longer reproduce** — they appear to have been fixed as part of the broader
refactor and dashboard/POS work done since, not by this pass itself (this pass only fixed a
broken test file so the probes could run again; **no application code was changed to make
these findings pass** — see the note at the end of this section). One finding (A18) was
re-checked and is **still present**. Three findings (A16, A17, plus the low-risk missing-
session observation) were checked by source review only, not by re-running a live probe —
they read as fixed but are marked accordingly. The deployment-configuration checks (DNS/TLS,
real secrets, browser E2E across all pages, dependency vulnerability scan, load testing,
backup/restore) were **not re-run this pass** — they were never something a backend-logic
audit could establish, and nothing below should be read as having verified them.

**Decision: CONDITIONAL — not NO-GO, not an unqualified GO.** The specific critical/high
defects that justified the original NO-GO (tenant isolation, privilege escalation, payment
integrity, device suspension bypass) are now verified fixed. Production readiness still
requires: closing A18 (promotions/deals reward flow), the deployment-configuration work in
§"Deployment configuration" below (unchanged from the original audit — still not done), and a
full browser walkthrough (§E2E_ACCEPTANCE_TEST.md / LOCAL TESTING GUIDE.md), since no browser
automation was available in either audit pass.

## What changed since 5 September, and how this pass verified it

The 5 September audit's 14 backend probes (`tests/audit_deployment_checks.py`) no longer
compiled after the refactor — they referenced the removed `Restaurant`/flat-option model. This
pass rewrote them against the current `Business`/`Variant`/`Add-on` model (same intent, same
assertions) plus added one new probe (the previously-unmounted legacy `/api/v1/tenants`
router) and two D7 add-on-pricing probes, for **15 probes total**, then ran them against the
current codebase with a rollback-isolated Postgres fixture — nothing was mocked. Where a probe
that used to assert "the defect reproduces" now fails to reproduce, that is because the
underlying code changed, not the probe's expectations (the `sale()` helper itself needed
several unrelated fixes — a required `variant_id`, a matching Variant Option snapshot, and a
server-reverified `unit_price` — precisely because three *new* guardrails now reject a
malformed sale before it can even test the old defect; each of those was confirmed as an
independent, additional fix, not a probe bug being papered over).

| Check | Result |
|---|---|
| Backend suite (`pytest -q`, excludes the explicitly-invoked audit probes) | 481 passed (93.28s) |
| Audit probes (`pytest tests/audit_deployment_checks.py -q`) | 15 run: 10 confirm a fix (old "reproduces" test now fails to reproduce), 4 directly assert new correct behavior and pass, 1 still reproduces (see A-missing-shift below) |
| Flutter analyzer (`flutter analyze`) | No issues found |
| Flutter tests (`flutter test`) | 14 passed |
| Live backend round-trip (real Electronics-template tenant, real device activation, real sale with a Variant + two Add-ons) | Sync payload parsed correctly by the Dart DTOs; sale accepted; server-side add-on price re-verification (D7) confirmed; branch stock deducted 10→9 |
| Database migrations | Single fresh baseline `0eb716adc2b6_initial_schema` → `f2abd477c3dd_product_sku_warranty_specs` (head as of this pass, 13 September); the old 20-plus-migration chain named in the original audit no longer exists — a pre-refactor database cannot upgrade in place. **Stale as of 20 September** — the real head has since moved past this (refunds/roles/discount work added several more migrations); this row is a point-in-time record of the migration-chain reset, not a current reference. Always get the real head with `alembic heads`, never from this file. |
| pos_preview app | No longer exists in the repository — A24 is moot, not merely "excluded" |
| Browser end-to-end tests | Still not run: browser automation tooling still unavailable in this environment |
| Deployment configuration (DNS/TLS, secrets, dependency vuln scan, load/backup) | Not re-checked this pass — see the original findings under "Deployment configuration" below, carried forward unverified |

## Isolation verdict

| Boundary | 5 Sept verdict | 13 Sept verdict |
|---|---|---|
| Tenant A versus Tenant B | **Failed:** global legacy tenant API plus cross-tenant relationship writes | **Fixed, re-verified:** legacy `/api/v1/tenants` router confirmed not mounted (404); branch assignment (A04), role assignment (A03), and catalog product scoping (A05) now all reject cross-tenant references |
| Tenant user versus tenant administrator | **Failed:** self-escalation through branch availability and underprotected role/user APIs | **Fixed, re-verified:** `PUT /users/{id}/branches` now requires `users.manage` (403 `PERMISSION_DENIED`) |
| Platform versus tenant authority | Legacy tenant APIs and platform suspension bypass defeated the boundary | **Fixed, re-verified:** legacy router unmounted; `DeviceService.reactivate()` now blocks a `PLATFORM`-scoped suspension explicitly |
| Branch A versus Branch B | Partial query scoping; assignment/availability/reactivation gaps | **Improved, re-verified for the specific probed paths:** branch-ownership check added to `set_branch_assignment`; POS availability enforcement (module + branch + device + user status) confirmed via A06/A07/A09 probes. Not exhaustively re-audited beyond the original findings' specific paths. |
| Cashier permission / Free Guest | Checkout tests pass; upstream escalation allowed unauthorized self-grants | **Fixed, re-verified:** the upstream escalation path (A02) that made the earlier feature-level Free Guest validation insufficient is closed |
| Offline device versus server | Not reliable: identity, deduplication, removal propagation, retry gaps | **Improved:** sale identity/dedup (A14) and periodic retry (A15) fixed, re-verified by source. Catalog removal propagation (A16) and tenant-reactivation isolation (A17) read as fixed via the full-replace sync strategy, but were checked by source review only, not a live multi-device probe. |

## Findings

### Fixed, re-verified this pass by re-running a probe

**A01 — Legacy tenant router.** `api/v1/tenants.py` carries an explicit code comment that it
is not mounted; `test_fixed_legacy_tenants_router_not_mounted` confirms `GET
/api/v1/tenants/{other_tenant_id}` now 404s instead of returning the other tenant's data.
Evidence: [apps/backend_fastfood/api/v1/tenants.py:1-6](apps/backend_fastfood/api/v1/tenants.py#L1-L6).

**A02 — Self-escalation via branch availability.** `PUT /api/v1/users/{id}/branches` now 403s
with `{"code":"PERMISSION_DENIED"}` for a user with no permissions, instead of letting them
set `all_branches:true` on themselves and then grant themselves `can_free_guest`.
Evidence: `test_reproduces_self_escalation_then_free_guest_grant` now fails at the first
`PUT`, asserting a `403`.

**A03 — Cross-tenant role assignment.** `RoleService.assign_user_role()` now calls
`_check_user()`, which requires `User.tenant_id == tenant_id` before attaching a role — a
Tenant A role can no longer be assigned to a Tenant B user.
Evidence: [apps/backend_fastfood/services/role_service.py:177](apps/backend_fastfood/services/role_service.py#L177) now raises `NotFoundError("User not found.")`.

**A04 — Cross-tenant branch assignment.** `UserService.set_branch_assignment()` now verifies
every submitted `branch_id` belongs to the caller's tenant before accepting it.
Evidence: [apps/backend_fastfood/services/user_service.py:276](apps/backend_fastfood/services/user_service.py#L276) now raises `NotFoundError("Branch not found in this tenant.")`.

**A05 — Cross-tenant product in a POS sale.** `checkout_validation.validate_catalog()` now
scopes the product lookup by `Business.tenant_id`, rejecting a sale item referencing another
tenant's product.
Evidence: [apps/backend_fastfood/services/checkout_validation.py:25](apps/backend_fastfood/services/checkout_validation.py#L25) now raises `ValidationError("Product is unavailable in this tenant.")`.

**A06 — Suspended device / inactive cashier can still sell.** `POST /api/v1/pos/sales/` now
403s with `{"code":"DEVICE_SUSPENDED"}` when the device is suspended, before the sale is ever
built.

**A07 — Deactivated tenant/user retains dashboard access.** `GET /api/v1/users/` (and, by the
same guard, every other `get_current_user`-gated route) now 401s with "Account is inactive or
unavailable" once the tenant or user is deactivated — a previously-issued token is no longer
honored.

**A08 — Tenant action undoes a platform device suspension.** `DeviceService.reactivate()`
explicitly checks `suspended_scope == PLATFORM` and refuses to lift it from the tenant side.
Evidence: [apps/backend_fastfood/services/device_service.py:254](apps/backend_fastfood/services/device_service.py#L254).

**A09 — Disabled modules remain usable through POS.** `api/v1/pos/_guards.py`'s
`operational_cashier` now checks `tenant_enabled_modules()` itself and 403s with
`{"code":"MODULE_DISABLED"}` — the entitlement check that previously existed only on the
tenant-dashboard router now also covers the POS sale path.
Evidence: [apps/backend_fastfood/api/v1/pos/_guards.py:71-73](apps/backend_fastfood/api/v1/pos/_guards.py#L71-L73).

**A10 — Sales can complete without payment.** `PosSaleService.create()` now rejects a sale
outright when `not data.payments or paid < data.total or paid - data.total > cash`.
Evidence: [apps/backend_fastfood/services/pos_sale_service.py:108](apps/backend_fastfood/services/pos_sale_service.py#L108).

**A11 — Cash change counted as collected revenue.** `Payment` now stores `amount` net of
returned change and `tendered_amount` (the raw amount handed over) as two separate columns;
payment-method reporting sums the net `amount`, not the tendered figure.
Evidence: [apps/backend_fastfood/services/pos_sale_service.py:251-263](apps/backend_fastfood/services/pos_sale_service.py#L251-L263).

**A12 — Repeated refunds can exceed the original sale.** A full refund now flips `Sale.status`
away from `COMPLETED`; a second refund attempt against the same sale is rejected with
`ValidationError("This sale cannot be refunded.")` rather than silently accepted again.
Evidence: [apps/backend_fastfood/services/refund_service.py:138](apps/backend_fastfood/services/refund_service.py#L138).

**A13 — Valid paid customizations fail checkout.** The structural cause (options carrying a
price the frontend included in `lineTotal` but the backend's total check ignored) no longer
exists — Variant Options never carry a price (spec A1/D4); pricing lives on Add-ons, which are
always re-verified server-side against `AddonItem.price_delta` (D7). Verified both directions:
a correctly-priced Add-on selection is accepted end to end
(`test_fixed_addon_priced_customization_now_accepted`), and a client that lies about an
add-on's price (submits `price_delta: 0`) is still rejected because the server recomputes the
expected total from its own data (`test_fixed_tampered_addon_price_still_rejected`).

**A14 — Offline sales can collide or be misattributed.** `sale_repository.dart`'s sale number
is now a client-generated UUID formatted as `S<year>-<uuid-without-dashes>` — globally unique,
not a device-local counter — and `pos_sale_service.py`'s duplicate check now matches on
`data.id == existing.id` plus `device_id`/`user_id`, not just a same-branch sale-number string
match.

**A15 — Offline upload retry didn't run on the periodic tick.** `sync_service.dart`'s `_tick()`
(fired by the 5-minute `Timer.periodic`, by the initial app start, and by a connectivity
transition) now calls `_uploadPending()` before `_deltaSync()` in all three cases — a queued
sale is retried on every periodic tick, not only at the moment connectivity flips.
Evidence: [apps/flutter_app_fastfood/lib/services/sync_service.dart:41-67](apps/flutter_app_fastfood/lib/services/sync_service.dart#L41-L67).

**A19 — Stored dashboard text inserted as HTML.** `promotions.html` now wraps every
interpolated value (`p.name`, `p.promo_code`, the discount/type labels) in `escapeHTML()`
before building `tbody.innerHTML`.
Evidence: [apps/web_fastfood/tenant/promotions.html:513-516](apps/web_fastfood/tenant/promotions.html#L513-L516). Not re-audited across all 35 HTML pages — only the specific sink named in the original finding.

**A20 — Authentication throttling not enforced.** `core/auth_limits.py`'s `limit_auth()` (an
`auth_rate_limits`-table-backed check reading `max_login_attempts`) is now imported and called
from `api/v1/pos/auth.py`, `api/v1/auth.py`, and `api/platform/auth.py` — device activation,
tenant login, and platform login are all now rate-limited.

**A21 — Kitchen module was management-only.** `web_fastfood/tenant/kitchen.html` is now a real
operational queue with a `PENDING → PREPARING → READY → SERVED` status workflow driven by
`preparation_status` on each sale item, not just station CRUD.

**A22 — Unfinished "coming soon" UI.** The "Plan change coming soon" button previously on
`platform/tenant-detail.html` is no longer present.

**A23 — Android release compiled with debug signing.** `android/app/build.gradle.kts` now
hard-fails (`throw GradleException(...)`) any release build task when `android/key.properties`
doesn't exist, and the `release` build type's `signingConfig` only resolves to a real keystore
— it is no longer possible to produce a debug-signed release APK/AAB by omission.
Evidence: [apps/flutter_app_fastfood/android/app/build.gradle.kts:14-18,43-55](apps/flutter_app_fastfood/android/app/build.gradle.kts#L14-L55).

**A24 — Separate preview app incomplete.** `apps/pos_preview` no longer exists in the
repository. Moot rather than fixed — there is nothing left to exclude.

### Confirmed fixed by source review this pass (not re-run as a live probe)

**A16 — Deleted/unassigned catalog records remained on the POS.** `sync_repository.dart`'s
`fullSync()` wraps `clearCatalog()` + a full re-apply in one transaction, and `deltaSync()`
simply calls `fullSync()` — every sync (periodic or forced) is a full replace, which by
construction propagates removals and option-only edits. This is the current, already-shipped
behavior (present before this session's Flutter refactor began, not a change made to pass this
finding) — a live two-device probe was not re-run to confirm the removal actually reaches a
running app.

**A17 — Reactivating a tablet for a new shop retained old data.** `onboarding_notifier.dart`'s
`activate()` calls `db.clearDeviceData()` — which clears the catalog *and* local sales *and*
settings — before pairing with a new activation code. Same caveat as A16: read from source, not
re-probed live on a physical/emulated device across two activations.

**Shift/session attribution (resolved for the supported POS client).** The Flutter checkout now
sends the active `session_id` for online and offline sales, and the backend validates the supplied
shift. `PosSaleCreate.session_id` remains optional only for compatibility with older/manual
clients; the device/cashier/time-window fallback remains for those requests. Release acceptance
must verify new POS sales carry a shift ID and that Sales/Reports filters find them.

### Still open

**A18 — Promotions and deals are not complete end to end.** Re-checked directly this pass:
`apps/flutter_app_fastfood/lib/core/models/sync/pos_sync_promotion.dart` still has no
`reward_product_id`/`reward_category_id`/`reward_quantity`/`reward_discount_type`/
`reward_discount_value` fields, even though the backend's `PosSyncPromotion` schema carries
them (`apps/backend_fastfood/schemas/pos_sync.py`) and `services/offer_service.py` computes
BXGY/FREE_ITEM rewards server-side. No POS-side flow that applies a reward automatically was
found. The dealId-mapping part of the original finding ("Flutter maps dealId from the item ID
rather than the parent deal ID") reads as already correct in the current
`sync_repository.dart` (`dealId: d.id`, the parent deal, not the item) — only the missing
reward fields/flow remain open.

### Not re-verified this pass — carried forward from 5 September unchanged

Everything under "Deployment configuration" below: live DNS/TLS/firewall, fresh-server
provisioning, clean-database migration rehearsal (the migration chain itself changed — see
above — so this specifically needs re-rehearsing against the new single-baseline chain),
production secrets delivery, backup restoration, media durability, load/concurrency, true
multi-device offline recovery, real printer/share integration, SMTP delivery, dependency
vulnerability feeds, and browser interaction across all pages. None of these were in scope for
either audit pass — they require a real staging server and, for the browser checks, tooling
that was not available in this environment either time.

## Module completeness matrix

| Module | 13 September state |
|---|---|
| Platform accounts, plans, onboarding | Implemented; legacy tenant route exposure closed (A01) |
| Platform/tenant dashboards | Pages and API integrations exist; promotions.html XSS sink closed (A19), one unfinished "coming soon" affordance removed (A22); no full browser acceptance run performed |
| Tenants / Businesses | `Business` replaces `Restaurant` (1:1 with Tenant, spec A2); legacy tenant root API confirmed unmounted |
| Branches / user assignment | CRUD exists; the specific cross-tenant assignment and self-escalation paths from the original audit are closed (A02, A04) |
| Roles / permissions | The specific cross-tenant role-assignment path is closed (A03); not re-audited as a complete access-control boundary beyond the originally-probed paths |
| Devices / activation | Lifecycle, code expiry, and now enforced rate limiting (A20); platform-suspension integrity closed (A08); sale-time enforcement (device + module) closed (A06, A09) |
| Menu / categories / Variants / Add-ons | Colors are create-time priced/stocked Variants; product detail edits existing color prices and shows overall/color/branch totals; Variant Selections are shared inventory components; Add-ons remain separate price deltas; sku/specs/warranty are template-gated |
| POS sales / checkout | Unpaid-completion (A10) and paid-customization-rejection (A13) blockers closed; Add-on pricing server-re-verified end to end (D7) |
| Payments | Tendered vs net-collected now stored separately (A11); JazzCash/EasyPaisa/card labels are still not evidence of a live gateway settlement integration |
| Free Guest | Zero-value receipt/inventory/permission checks implemented; the upstream self-escalation path that undermined it (A02) is closed |
| Refunds | Cumulative-refund-over-original-value path closed (A12) |
| Inventory | Quantity ledger + per-branch cache (`VariantBranchStock`); dashboard and tests use `/variants` plus `/variants/{id}/stock...`; opening/add/adjust/deduct/restore and color-level totals tested |
| Shifts / reconciliation | Change no longer counted as revenue (A11); supported Flutter checkout supplies `session_id`; compatibility fallback remains for legacy/manual requests |
| Promotions / deals | Dashboard CRUD exists; POS reward application and the reward-field sync gap are **still open** (A18) |
| Kitchen / KDS | Now a real `PENDING→PREPARING→READY→SERVED` operational queue (A21), not management-only |
| Expenses / employees / salaries | Unchanged from the original audit — permission checks and service tests exist; no full browser or payroll business acceptance sign-off performed either pass |
| Subscriptions / billing | Unchanged from the original audit |
| Reports | Payment-method reporting reflects net collected cash, not tendered (A11); Sales and all report panels support cashier/shift scoping, and the PostgreSQL monthly-grouping regression is covered |
| Activity / audit | Unchanged from the original audit |
| Offline sync | Sale identity/dedup (A14) and periodic retry (A15) closed; full-replace sync (A16) and reactivation isolation (A17) read as already-correct by source, not live-reprobed |
| POS preview | No longer exists (A24 moot) |

## Deployment configuration and remaining external checks

**Unchanged from the 5 September audit — not re-checked this pass.** The database migration
chain referenced there no longer exists (see "What changed" above); every other item —
environment identification, CORS, SECRET_KEY, SMTP configuration presence, the nginx template
still using `app.example.com` over HTTP, `/health` being liveness-only — was not re-verified
and should not be assumed current. Re-run this section fresh against a real staging target
before go-live; do not carry forward the specific migration-name detail from 5 September
(`461fa3562c3e`) — the current head is `f2abd477c3dd`.

Not verified in either audit pass: live DNS/TLS/firewall, fresh-server provisioning,
clean-database migration rehearsal, production secrets, backup restoration, media durability,
load/concurrency, true multi-device offline recovery, real printer/share integration, SMTP
delivery, dependency vulnerability feeds, or browser interaction across all HTML pages. No live
card/mobile-wallet gateway settlement was established either pass.

## Release order and acceptance criteria

1. ~~Close global tenant endpoints, privilege escalation, cross-tenant relationship writes and
   current-state authorization gaps.~~ **Done, re-verified this pass (A01–A09).** Convert the
   15 audit probes in `tests/audit_deployment_checks.py` into a permanently-collected
   regression suite (rename off the `audit_` prefix, or add it to the default pytest path) so
   these can't silently regress.
2. ~~Enforce authoritative checkout settlement, prices/options/discount rules, cumulative
   refunds and platform suspension ownership.~~ **Done, re-verified this pass (A10–A13).**
3. ~~Repair offline identity, globally unique/idempotent submission, queue retry.~~ **Done,
   re-verified this pass (A14, A15).** Catalog removal propagation and tenant-local storage
   isolation (A16, A17) read as already correct — confirm with one live two-device walkthrough
   rather than treating source review as sufficient sign-off.
4. **Still open:** finish the promotions/deals reward flow end to end (A18) — add the missing
   reward fields to `PosSyncPromotion` (Flutter) and build the POS-side application of a BXGY/
   FREE_ITEM reward, or explicitly scope promotions/deals out of this release and disable them
   in the POS.
5. Run full browser workflows for platform owner/manager/viewer, tenant owner and restricted
   cashier across two tenants (one per Business Template — Fast Food and Electronics-style, to
   exercise the template-gated pricing/sku/tracking fields) and at least two branches/devices
   each — see `E2E_ACCEPTANCE_TEST.md`. Still not done in either audit pass.
6. Provision a staging server with HTTPS, correct CORS, real release signing (now enforced by
   the build itself — A23) and the current migration head `f2abd477c3dd`; test restore and
   monitoring. Approve production only after step 4 and this step pass acceptance tests.

## Reproduction artifacts

- [Audit probes](apps/backend_fastfood/tests/audit_deployment_checks.py) — rewritten this pass
  for the current model; run explicitly, not auto-discovered by the regular `test_*.py`
  pattern (the file itself is not named `test_*.py`). A `test_reproduces_*` name that now
  **fails** means that finding is fixed; a `test_fixed_*` name that **passes** directly asserts
  correct behavior; `test_reproduces_missing_shift_attribution` passing means that specific
  low-risk observation still holds.
- The 5 September reproduction artifacts referenced by the original audit
  (`audit-test-results.txt`, `audit-reproduction-results.txt`, the Flutter/preview
  analyzer/test/build logs, `audit-links.json`) describe the pre-refactor codebase and were not
  regenerated this pass — treat them as historical, not current.

Run the backend probes from `apps/backend_fastfood` with `DEBUG` set to a valid boolean:
`python -m pytest tests/audit_deployment_checks.py -q`. Use a local test database with the
current migration head (`f2abd477c3dd`).
