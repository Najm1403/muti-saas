# Documentation map and sources of truth

Use this page to choose the correct document. Each subject has one primary source of
truth; supporting documents have a narrower purpose and must link back to the primary
one. When documentation and executable behavior disagree, the current models,
migrations, API schemas, and tests are authoritative and the documentation must be
corrected in the same change.

## Product and architecture

| Subject | Source of truth | Purpose |
| --- | --- | --- |
| Foundational domain model | [`apps/COMPLETE-IMPLEMENTATION-SPEC.md`](apps/COMPLETE-IMPLEMENTATION-SPEC.md) | Tenant/Business/Branch, catalog, Variant, Add-on, stock, and offline-sale foundations; operational feature guides below own later workflows |
| Runtime ownership and call paths | [`EXECUTION FLOW.md`](EXECUTION%20FLOW.md) | Page-to-API-to-service and Flutter-to-API execution map |
| Business Templates | [`BUSINESS_TEMPLATE_GUIDE.md`](BUSINESS_TEMPLATE_GUIDE.md) | Creating, applying, and maintaining templates |
| Web visual system | [`apps/web_fastfood/STYLE_GUIDE.md`](apps/web_fastfood/STYLE_GUIDE.md) | Shared UI, responsive, and accessibility conventions |
| API contract | Running backend `/docs` plus checked-in schemas | OpenAPI is generated from the implemented FastAPI routes and Pydantic schemas |
| POS activation | [`apps/flutter_app_fastfood/ACTIVATION_CONTRACT.md`](apps/flutter_app_fastfood/ACTIVATION_CONTRACT.md) | Activation payload, tokens, lifecycle, and device errors |
| Future roadmap | [`FUTURE_ROADMAP.md`](FUTURE_ROADMAP.md) | Planned initiatives (recipes, purchasing, forecasting, AI/agents), audited against what already exists, phased with estimates |

## Operational feature guides

| Subject | Source of truth |
| --- | --- |
| Variant and branch inventory | [`apps/backend_fastfood/docs/INVENTORY.md`](apps/backend_fastfood/docs/INVENTORY.md) |
| Sales history and reports | [`apps/backend_fastfood/docs/SALES_AND_REPORTING.md`](apps/backend_fastfood/docs/SALES_AND_REPORTING.md) |
| Bill cancellation and returns | [`apps/backend_fastfood/docs/POS_RETURNS_AND_CANCELLATIONS.md`](apps/backend_fastfood/docs/POS_RETURNS_AND_CANCELLATIONS.md) |
| Promotions and deals | [`apps/backend_fastfood/docs/PROMOTIONS_AND_DEALS.md`](apps/backend_fastfood/docs/PROMOTIONS_AND_DEALS.md) |
| Free Guest checkout | [`apps/backend_fastfood/docs/free_guest.md`](apps/backend_fastfood/docs/free_guest.md) |
| Employee attendance and `pos.operate` | [`apps/backend_fastfood/docs/ATTENDANCE.md`](apps/backend_fastfood/docs/ATTENDANCE.md) |

## Testing and release

| Subject | Source of truth | Supporting document |
| --- | --- | --- |
| Full local setup | [`LOCAL TESTING GUIDE.md`](LOCAL%20TESTING%20GUIDE.md) | [`apps/backend_fastfood/LOCAL_TESTING.md`](apps/backend_fastfood/LOCAL_TESTING.md) contains backend feature acceptance only |
| End-to-end sign-off | [`E2E_ACCEPTANCE_TEST.md`](E2E_ACCEPTANCE_TEST.md) | A concise acceptance checklist, not setup instructions |
| Production deployment | [`deploy/DEPLOYMENT-RUNBOOK.md`](deploy/DEPLOYMENT-RUNBOOK.md) | The only deployment procedure: readiness, first VPS, builds, later releases, verification, backup, and rollback |
| POS builds | [`apps/flutter_app_fastfood/BUILD_CLIENTS.md`](apps/flutter_app_fastfood/BUILD_CLIENTS.md) | Windows, installer, Android, signing, printers, and build-time API URL |
| Git and maintenance | [`deploy/GIT-GITHUB-MAINTENANCE.md`](deploy/GIT-GITHUB-MAINTENANCE.md) | GitHub workflow, versioning, releases, hotfixes, and long-term maintenance |
| Change ownership | [`deploy/CHANGE-OWNERSHIP.md`](deploy/CHANGE-OWNERSHIP.md) | Which application layers and compatibility checks belong to each feature type |
| Email | [`deploy/EMAIL-SETUP.md`](deploy/EMAIL-SETUP.md) | SMTP and password-reset setup |

`AUDIT_HISTORY.md` is dated audit evidence, not an implementation specification.
Do not copy old findings from it into current behavior without verifying the code and
tests. `FUTURE_ROADMAP.md` is planning, not an implementation specification either — it
describes work that has not been built yet and must be re-verified against the codebase
before anyone starts on it, since the current state it was audited against will drift.
Component README files are entry points only and should link to the sources above
instead of repeating their procedures.
