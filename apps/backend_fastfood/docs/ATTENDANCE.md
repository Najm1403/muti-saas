# Employee attendance (clock-in/out)

This guide covers the data model, API, permission model, and the POS/dashboard
workflows for attendance. It is independent of `CashierSession` (cash-drawer
shifts) — an employee can clock in for attendance without ever opening a POS
shift, and a POS shift can only be opened by someone who separately holds
`pos.operate` (see "Permission model" below).

## Why a separate feature from cashier shifts

`CashierSession` already tracks open/close per POS device, but it only exists
for staff who operate the register, is tied to a cash-drawer reconciliation
workflow, and requires a cashier login. Attendance needed to work for staff
who never touch the POS (kitchen, delivery, back office) and without forcing
them through the "open a shift" flow, so it is modelled as its own table and
API surface: `AttendanceRecord` (`models/attendance_record.py`).

## Data model

`attendance_records` — one row per clock-in/clock-out pair:

| Column | Notes |
| --- | --- |
| `tenant_id`, `branch_id` | Set from a server-verified source at creation, never trusted from client input as the sole source of truth — `branch_id` supplied by an admin (manual entry) is re-verified via `Branch → Business → tenant_id`. |
| `employee_id` | FK to `employees` — attendance is tied to the HR record, not a login. Every active employee can punch using their own `employees.pin_hash`, whether or not they're also a `User`. |
| `user_id` | Informational cross-reference to `employees.user_id` at punch time, when the employee also happens to be a User. Never required, never checked — a PIN punch authenticates purely against the employee's own PIN. Null for a dashboard manual entry or for an employee with no linked User. |
| `device_id` | The device the punch came from. Null for a manual entry. |
| `clock_in_at`, `clock_out_at` | `clock_out_at` null means still clocked in. |
| `method` | `pin` \| `manual` \| `biometric` (reserved for a future hardware integration — see "Future: biometric" below). |
| `source` | `pos_kiosk` \| `dashboard`. |
| `recorded_by_user_id`, `notes` | Who created/edited the row and why, when it wasn't the employee's own PIN punch. |

**Database-level integrity**: a partial unique index —
`ux_attendance_records_one_open_per_employee` on `(employee_id) WHERE
clock_out_at IS NULL AND deleted_at IS NULL` — guarantees at most one open
record per employee even under a concurrent double-tap. The service layer
catches the resulting `IntegrityError` and returns a friendly validation
error rather than a 500.

Every read is scoped by `tenant_id` first; `employee_id`/`branch_id` are
additionally re-verified against the calling tenant before use in any write
path that accepts them from client input (`services/attendance_service.py`).

## Employee ↔ User linkage

Attendance authenticates against the employee's own PIN
(`employees.pin_hash`, set from **Employees → Set PIN**), never against a
`User`'s POS PIN or password. This is deliberate: most employees who need to
clock in (kitchen, delivery, back office) should never be able to log into
the POS register at all, and requiring a `User` account just to punch would
force every one of them through cashier-login permission gates that have
nothing to do with attendance.

A `User` (POS/dashboard login) can only be created by promoting an existing,
active `Employee` — see **Users → Add User**, which now picks from
`GET /employees?status=active&unlinked=true` instead of free-typing a name.
This sets `Employee.user_id` (unique per employee — one employee links to at
most one `User`) and the login's `full_name` is always taken from the
Employee record, so the two can never drift apart. This is also what makes
`AttendanceRecord.user_id` populate: it's a byproduct of how the `User` was
created, not something attendance itself manages.

Before this design, `Employee.user_id` existed in the schema but nothing in
the app ever set it, so every PIN punch failed with "No employee record is
linked to this login" — the bug this section's design fixes. If a tenant's
existing data still has a `User` created the old way (free-standing, no
linked employee), it simply has no bearing on attendance; that user can keep
using the POS as before, and any employee who needs to clock in gets an
attendance PIN independent of it.

## Permission model — and the gap this closes

Before this feature, `POST /api/v1/pos/auth/staff-pin` and `POST
/api/v1/pos/auth/cashier` minted a full cashier session for **any** active,
branch-assigned user — there was no check on whether the user held any role
or permission at all, only on specific actions afterward (e.g.
`sales.discount`). That was a tolerable gap while PINs were only ever handed
to actual cashiers, but attendance means PINs now go to every employee who
should be able to clock in, including staff who must never operate the
register.

Both login endpoints now additionally require the new `pos.operate`
permission (or the existing Admin/Owner/Manager wildcard bypass in
`get_user_permissions()`) before minting a cashier token:

- `attendance.view` — read the register and live status.
- `attendance.manage` — manual entries and corrections.
- `pos.operate` — required to open a cashier session at all (PIN or
  password login). Punching attendance does **not** require this permission
  and never mints a cashier token, by design (`api/v1/pos/attendance.py`
  depends on `operational_device`, not `operational_cashier`).

**Fresh install**: `pos.operate` is part of the seeded permission catalog
from the very first migration — there is no transition or backfill step for
a new tenant. Every role must be explicitly granted `pos.operate` from
**Roles & Permissions** in the tenant dashboard before its members can open
a cashier session, exactly like any other permission. A PIN-holding user
whose role (or lack of one) was never granted `pos.operate` can clock in via
attendance but cannot operate the till — that is the intended behavior, not
a bug: a PIN alone was never meant to imply cashier access.

(Historical note: on a database created before this permission existed, the
migration that introduced it backfilled `pos.operate` onto every role that
already held at least one permission, so existing "Cashier"-style roles kept
working unchanged after upgrade — it deliberately did not grant it to a role
with zero permissions, since that combination only ever worked by omission.
That transition is now baked into the single initial migration for any new
install and no longer applies going forward.)

Attendance-only staff (kitchen/delivery/office) need no role or permission
grant at all — they don't need to be a `User` in the first place. Just add
them as an `Employee` and set a PIN from **Employees → Set PIN**; they can
clock in/out with no POS access whatsoever. The `pos.operate` gate above only
matters for employees who are *also* promoted to a `User` for cashier/admin
access — that grant controls whether their login can open a cashier session,
not whether they can punch attendance.

## Module toggle

Attendance is its own tenant-dashboard module (`core/modules.py`, key
`"attendance"`, group "Back office") — separate from the "Employees (HR)"
module, so a tenant can run payroll records without punch-clock tracking or
vice versa. Like every optional module, an absent/empty `hidden` list on the
tenant's Business Template means it is visible by default; disable it per
template from **Module Templates** if a tenant shouldn't have it. The POS
punch/status endpoints independently re-check the module server-side
(`api/v1/pos/attendance.py`), so disabling it also blocks POS clock-in
immediately, not just the dashboard page.

## POS workflow

**Clock In / Out** is reachable from the staff picker (before any login) and
from the dashboard app bar (while a cashier is logged in) — it is
deliberately exempted from the app's activation/login/shift redirect chain
(`app.dart`'s `alwaysReachableRoutes`) so an attendance-only employee can
always reach it.

1. Tap **Clock In / Out** → pick your name from the grid, populated by
   `GET /api/v1/pos/attendance/staff` (every active employee for this
   branch — independent of the cashier picker, which only lists `User`
   accounts) → enter your PIN on the same PIN pad widget. A tile for an
   employee with no PIN set yet is shown greyed-out with "No PIN set"
   instead of opening the pad.
2. The server toggles: no open record for today → clocks in; an open record
   exists → clocks out. One button, no separate "in"/"out" choice to get
   wrong.
3. Tiles for currently-clocked-in staff show a green border and "In since
   HH:MM".

This flow calls `POST /api/v1/pos/attendance/punch` with the device token
only, authenticating against `employees.pin_hash` — it can never produce a
cashier token, regardless of the calling employee's role or whether they
have a `User` account at all.

**Known limitation**: unlike sales, a punch is online-only in this release —
it is not queued locally when the device is offline. If this becomes an
issue in practice, the offline-queue pattern already used for sales
(`LocalSalesTable` in the Flutter app) is the template to follow.

## Tenant dashboard workflow

**Attendance** (sidebar, under Back office) has three parts:

1. **Currently clocked in** — pick a branch to see a live list of who's in
   and since when.
2. **Register** — filterable by branch, employee, and date range; shows
   clock-in/out, duration, method, and who recorded it.
3. **Manual entry / Correct** (`attendance.manage`) — add an entry for staff
   without device access, or fix a missed clock-out. Every manual entry and
   correction requires a reason and is written to the Activity Log
   (`AuditLog`, module `attendance`) with the acting admin's name.

## Future: biometric

The `attendance_records.method` column already accepts `"biometric"` as a
value (`schemas/attendance.py::ATTENDANCE_METHODS`), and every report/query
in this doc groups by `method` already, so the register and audit trail need
no changes to support it. The current `POST /pos/attendance/punch` endpoint
only accepts `employee_id` + `pin`, though — a biometric integration (e.g. a
DigitalPersona USB reader on a Windows POS device) would need either a new
request variant on this endpoint or a sibling endpoint that accepts a
resolved `employee_id` plus a device-side proof of the match instead of a
PIN. Fingerprint capture and matching should happen locally on
the device — enroll and match on-device, never ship a raw fingerprint
template to the server — so the endpoint only ever needs to learn the
already-resolved employee id and a success flag. Budget that endpoint plus
the client capture UI as its own piece of work; nothing else in this feature
should need to change for it.
