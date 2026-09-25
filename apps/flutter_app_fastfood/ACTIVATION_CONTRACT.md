# POS device activation & lifecycle — API contract

This is the backend contract for the Flutter POS app. No Flutter code is included here;
it describes exactly which endpoints to call and how to react.

## 1. First install — the only screen

```
            LOGO
      Activate this POS
   Enter activation code
          [ 5 8   3 2 ]
          [ Activate ]
   Internet connection required
```

The tenant admin created the device in the web dashboard (name + branch + purpose) and
was shown a **4‑digit activation code** (valid 15 minutes, one‑time). The user types only
that code.

### Request
```
POST /api/v1/pos/auth/activate
Content-Type: application/json

{
  "activation_code": "5832",        // "58 32" is also accepted
  "platform": "android",            // optional — "android" | "windows" | ...
  "app_version": "1.4.0"            // optional
}
```

### Response 200
```json
{
  "device_token": "<JWT, ~30 days>",
  "device_id": "uuid",
  "device_name": "Counter POS 2",
  "device_type": "POS",
  "branch_id": "uuid",
  "branch_name": "Main Branch",
  "business_id": "uuid",
  "business_name": "Storixx",
  "tenant_id": "uuid",
  "currency": "Rs."
}
```

Persist **all** of these locally (secure storage). The app never asks for Shop ID / branch /
device type again — they are baked into `device_token` and the stored context.

### Errors
`422 { "detail": "..." }` — invalid / expired / already‑used code, or the device was revoked.
Show the message and let the user retry or ask their manager for a new code.

## 2. Every normal launch

```
Open POS → Staff Login → PIN → Open/Resume Shift → POS
```

Using the stored `device_token` as `Authorization: Bearer <device_token>`:

| Step | Call |
|---|---|
| Staff grid | `GET  /api/v1/pos/auth/staff` |
| PIN sign‑in | `POST /api/v1/pos/auth/staff-pin` `{ user_id, pin }` → `cashier_token` (12 h) |
| (or) username login | `POST /api/v1/pos/auth/cashier` `{ username, password }` → `cashier_token` |
| Initial/full catalog sync | `GET  /api/v1/pos/sync/full` (device token) |
| Delta API (available for compatible clients) | `GET  /api/v1/pos/sync/delta?since=<iso>` (device token) |
| Upload offline sales | `POST /api/v1/pos/sync/upload` (cashier token) |
| Heartbeat | `PATCH /api/v1/pos/device/heartbeat` (device token) |

The current Flutter repository intentionally performs a transactional full catalog replace
for routine sync as well as first sync; its `deltaSync()` delegates to `fullSync()`. Do not
document or implement partial client-side merging unless the complete deletion/update
semantics are tested.

The employee sees `business_name` / `branch_name` and the staff list. UUIDs are retained
internally for scope and synchronization but are not used as display names.

## 3. Suspend / revoke handling (online only)

The tenant admin (or the platform) can **Suspend** (reversible) or **Revoke** (permanent) a
device. Enforcement happens the next time the device reaches the server — these endpoints
return **403** with a machine code:

```json
{ "detail": "This device is suspended.",  "code": "DEVICE_SUSPENDED" }
{ "detail": "This device has been revoked.", "code": "DEVICE_REVOKED" }
```

Endpoints that enforce it: `pos/sync/*`, `pos/device/heartbeat`, `pos/auth/cashier`,
`pos/auth/staff`, `pos/auth/staff-pin`.

App behaviour:
- `DEVICE_SUSPENDED` → block the POS UI, show "This device has been suspended. Contact your
  manager." Keep local data; retry on next launch / connectivity.
- `DEVICE_REVOKED` → wipe the stored `device_token` + context + local POS DB and return to the
  activation screen.

Offline devices can take ordinary sales from synchronized local catalog data until they
next connect. Activation, Free Guest authorization, bill cancellation, and sales returns
require the server; queued offline sales upload after connectivity returns.
