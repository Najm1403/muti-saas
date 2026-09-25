# Change ownership and compatibility

Use this map to identify which application layers a change normally touches. It is not
a release procedure; use [`DEPLOYMENT-RUNBOOK.md`](DEPLOYMENT-RUNBOOK.md) for all build,
deployment, verification, backup, and rollback commands.

| Change | Files to inspect | Required behavior |
| --- | --- | --- |
| Tenant dashboard UI | `apps/web_fastfood/tenant/*.html`, shared responsive assets | Browser calls tenant-scoped `/api/v1/...` routes; backend authorization remains authoritative |
| Platform administration | `apps/web_fastfood/platform/*.html`, `api/platform/*.py`, related services/schemas | Platform routes remain separate from tenant authority |
| Tenant API/business rule | `api/v1/<module>.py`, `services/*`, `schemas/*`, repository and tests | Validate permissions, tenant ownership, and branch scope in the backend |
| Database structure/data conversion | `models/*`, a new `alembic/versions/*` migration, schemas/services/tests | Keep one Alembic head; rehearse upgrade and restore with representative data |
| Module or plan entitlement | `core/modules.py`, `api/dependencies.py`, `shared/responsive.js`, route tests | UI hiding complements but never replaces server enforcement |
| Catalog and inventory | product/Variant/Add-on services and schemas, tenant menu/inventory pages | Add Product creates default/color Variants; Inventory owns later quantity changes |
| Cloud-to-POS catalog | `pos_sync_service.py`, `schemas/pos_sync.py`, POS sync API; Flutter sync models/repository/Drift | Server and client contract change together; full replacement remains transactional |
| POS sales/offline upload | POS sale/sync APIs and services; Flutter sale, checkout, SQLite, sync code | Preserve UUID idempotency, human invoice/cashier display, session attribution, stock validation, and retry safety |
| Reports | sales/report APIs/services, tenant sales/reports pages, Flutter report repository/DAO | Apply branch/date/cashier/shift scope consistently and deduplicate local/cloud receipts |
| Flutter screen/local schema | Flutter feature, model, database, DAO, API, and generated files | Add a Drift upgrade path, regenerate tracked sources, and test Windows and Android |
| Service or proxy | `deploy/fastapi.service`, `deploy/nginx.conf`, backend requirements/config | Review production paths, validate nginx, and restart only the affected service |
| POS/tenant authentication or permission gate | `api/v1/pos/auth.py`, `api/dependencies.py::get_user_permissions`, a permission-seed/backfill migration | A new gate on an existing login path can lock out an existing tenant's staff on upgrade — the migration must backfill the new permission onto every role that already had equivalent access, and the change must be called out in the release notes/runbook, not left to be discovered after deploy. See [`../apps/backend_fastfood/docs/ATTENDANCE.md`](../apps/backend_fastfood/docs/ATTENDANCE.md) for a worked example (`pos.operate`). |

## Compatibility rules

- A marketing version change does not require a database or sync-protocol change.
- Keep the Android build number increasing and align the Flutter version with the Windows
  installer version. Record the tested server/client combination in release evidence.
- If a POS payload becomes incompatible, change server and client serializers together,
  regenerate sources, add upgrade tests, deploy a backward-compatible server first where
  possible, and plan the installed-client rollout explicitly.
- Never copy an Alembic revision from documentation into a command. Verify one current
  head and deploy with `alembic upgrade head`.
- Multi-device offline stock cannot be guaranteed without coordination. The cloud must
  reject an upload that would violate stock, and the rejected local sale requires review.
- Add regression tests and update the relevant source-of-truth document in the same
  change. See [`../DOCUMENTATION.md`](../DOCUMENTATION.md).
