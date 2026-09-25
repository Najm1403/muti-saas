# Local pre-deployment testing

This guide is for local development only. Before using a real domain or distributing
POS clients, follow the production gates and exact server/client commands in
[`../../deploy/DEPLOYMENT-RUNBOOK.md`](../../deploy/DEPLOYMENT-RUNBOOK.md). Localhost
HTTP commands are never production build commands.

Use this checklist to test the complete setup before configuring DNS or deploying HTTPS.

## 1. Prepare the local API

Open PowerShell in `apps/backend_fastfood`:

```powershell
.\.venv\Scripts\Activate.ps1
$env:DEBUG='false'
.\.venv\Scripts\python.exe scripts\prepare_database.py
```

This applies all migrations and creates the initial Super Admin from `.env`
when no platform account exists. It is idempotent and never overwrites an
existing administrator or password. `run.py` performs the same preparation
automatically unless `--skip-db-prepare` is used.
Ensure PostgreSQL is running and that `DATABASE_URL` in `.env` points to the local test database. Start the API:

```powershell
python run.py --host 127.0.0.1 --port 8000 --reload
```

Check `http://127.0.0.1:8000/health` and open `http://127.0.0.1:8000/docs`.

## 2. Open the web client locally

The API development server already serves `apps/web_fastfood` at its root. Open `http://127.0.0.1:8000/platform/login.html`; API calls then use the same-origin `/api` path and no extra frontend configuration is required.

If you specifically need a separate static server, use `py -3 -m http.server 5500 --directory apps/web_fastfood` and configure `window.API_BASE_URL` to `http://127.0.0.1:8000` before the page scripts.

## 3. Run automated checks

```powershell
cd apps/backend_fastfood
$env:DEBUG='false'
pytest -q
```

The module-template regression checks are:

```powershell
pytest -q tests/test_module_templates.py
```

## 4. Manual tenant-integrity check

1. Log in as a platform super administrator and open **Module Templates**.
2. Confirm template cards edit template definitions only; template assignment is performed from a tenant's **Modules** tab.
3. Select Tenant A, apply a template, and confirm the replacement dialog.
4. Verify Tenant A's selected template and enabled modules, then open the usage count to see all assigned shops.
5. Open Tenant B and verify its template and modules did not change.
6. Edit Tenant A's individual modules and verify the template association is cleared.
7. Mark a template inactive and verify the API refuses to apply it.

## 5. Inventory and variant acceptance

Detailed operational references:

- [POS bill cancellation and sales returns](docs/POS_RETURNS_AND_CANCELLATIONS.md)
- [Creating promotions and deals](docs/PROMOTIONS_AND_DEALS.md)
- [Sales history and reporting](docs/SALES_AND_REPORTING.md)

1. In Tenant A, use **Add Product** to create a plain product with opening stock.
2. Create a second product with two Colors. Enter a sale price and opening stock for each color before saving.
3. Open each product's detail page. Confirm color membership stays as configured in Add Product and existing color prices remain editable.
4. Confirm **Overall Stock** is read-only and shows the all-branch total. For the colored product, confirm it also shows every color total and each color's per-branch quantities.
5. Confirm color names cannot be added or removed on product detail, while each existing color Variant's sale price remains editable.
6. Open Inventory and confirm it loads from `/api/v1/variants` and lists the tracked plain/default and color Variants. Search by product/color/Variant ID, then verify the in-stock and out-of-stock filters use the selected branch's balance.
7. Use Increase, Decrease, Set Stock, and History. Confirm each action uses `/api/v1/variants/{id}/stock...` and writes a stock adjustment row.
8. Sync one Windows POS and one Android POS and confirm both receive the same quantity-only Variant stock snapshot.
9. Sell one color. Confirm only that color Variant decreases, the product/color totals refresh, and a `sale` adjustment is recorded.
10. Attempt an offline oversell with repeated cart lines for the same Variant; checkout must aggregate the lines and reject it. Refund a valid sale and confirm only previously deducted quantity is restored.
11. Sign in as a user assigned to one branch. Confirm Inventory does not expose other-branch balances or permit a transfer involving another branch.
12. Open Reports as that user. Confirm every panel is limited to the assigned branch, a selected date's full day is included, and an unassigned `branch_id` is rejected.
13. Grant a POS cashier `sales.cancel`, complete a paid sale, and use **Cancel Order / Bill** before closing that cashier's shift. Confirm the complete bill is cancelled, tracked stock is restored, and a `CANCEL` refund audit row records the cashier and session.
14. Confirm another cashier/device and a later shift cannot cancel that bill. Remove `sales.cancel` and confirm cancellation and return submissions are rejected.
15. From **Sales Return**, enter an older invoice number, select one purchased item and quantity, and confirm the server calculates the amount from the original invoice. Verify the sale stays `COMPLETED` after a partial return and becomes `REFUNDED` only after every remaining item is returned.
16. Try returning more than the remaining purchased quantity, returning a cancelled bill, returning a fully returned bill, and returning a Free Guest order. Confirm each request is rejected without changing stock.
17. Close the shift and confirm Returns and Cancelled Bills have separate counts/payment breakdowns; cancelled sales are not also subtracted as returns.
18. Follow the date/cashier/shift and offline SQLite checks in [Sales history and
    reporting](docs/SALES_AND_REPORTING.md). Confirm the monthly report loads on
    PostgreSQL, date-range panels share the selected range, and all trend panels share
    the selected cashier and shift.

## 6. Promotions and deals acceptance

Follow the complete setup procedure in
[Creating promotions and deals](docs/PROMOTIONS_AND_DEALS.md), then verify:

1. An automatic promotion appears only when its quantity/amount/product/category
   conditions match.
2. A code-gated promotion is absent for a blank or incorrect code and appears for the
   exact saved code.
3. Specific-branch offers appear at an assigned POS and remain unavailable at an
   unassigned POS.
4. Fixed-price, flat-discount, percentage-discount, and free-item bundles calculate the
   expected server amount.
5. Changing the cart after applying an offer requires the cashier to find and apply it
   again.
6. Expired, inactive, exhausted, or deleted offers cannot be committed even if a client
   previously synchronized them.
7. A returned discounted sale refunds from its original sale values and does not use
   current catalog pricing.

## 7. Sales status and permission acceptance

1. Open **Sales** and confirm the status filter contains Completed, Cancelled, and
   Refunded, with no separate redundant status for cancellation.
2. Confirm every cancelled transaction appears under the single `CANCELLED` status
   after applying migrations.
3. Open **Users**, edit a normal user, and confirm every active system permission is
   displayed as a checkbox. Role-inherited permissions must already be checked.
4. As a tenant Admin/Owner/Super Admin, change the checklist and select **Apply
   permissions**. Confirm the change affects only that user and does not modify the
   shared role or another user assigned to it.
5. Sign in as a Manager or custom role and confirm the checklist is read-only and role,
   role-assignment, and permission mutation requests are rejected by the API.
6. Confirm Admin/Owner/Manager wildcard users show full access and require removal of
   that wildcard role before individual permission overrides can be applied.
7. Grant `sales.cancel` to a cashier and verify cancellation and return are allowed;
   remove it and verify both operations are rejected.

## 8. Attendance and `pos.operate` acceptance

Follow the full data model, permission model, and workflow in
[Employee attendance](docs/ATTENDANCE.md), then verify:

1. Enable the **Attendance** module for the test tenant's Business Template (Module
   Templates), then confirm the **Attendance** tab appears in the tenant dashboard sidebar.
2. Add a test **Employee** (Employees page) with no linked User account, set an
   attendance PIN (**Employees → Set PIN**). Confirm they appear on the POS **Clock In /
   Out** grid and can punch with that PIN, but never appear on the regular staff-picker
   cashier login (`WHO IS STARTING A SHIFT?`), since that lists Users only. Separately,
   promote a different active employee to a User (**Users → Add User**, select them from
   the employee list) while leaving that user on a role with no `pos.operate` grant —
   confirm the cashier-login staff picker rejects them
   with a clear "don't have permission to operate the POS" message.
3. Grant that role `pos.operate` and confirm cashier login now succeeds for the same PIN.
4. Confirm Admin/Owner/Manager wildcard users can operate the POS without an explicit
   `pos.operate` grant (existing wildcard bypass).
5. Clock a staff member in, confirm their tile shows "In since HH:MM" with a green
   border on the POS attendance grid, then clock them out and confirm the tile reverts
   and the dashboard **Currently clocked in** panel for that branch no longer lists them.
6. Attempt to clock in twice in a row without a matching clock-out in between (e.g. by
   quickly double-tapping) and confirm the second request either toggles cleanly or is
   rejected — never two simultaneous open records for the same employee.
7. On the dashboard, add a manual attendance entry for an employee, then correct an
   existing record (edit clock-out, or check "Clear clock-out"). Confirm both actions
   require a reason and appear in **Activity Log** under module `attendance`.
8. Confirm Tenant A's attendance register, live status, and manual-entry employee/branch
   pickers never show Tenant B's employees, branches, or records, and that attempting a
   manual entry with a cross-tenant `employee_id`/`branch_id` (e.g. via direct API call)
   is rejected with 404, not silently accepted.

## 9. Optional local HTTPS

For testing secure cookies and browser HTTPS behavior without deployment, use a locally trusted certificate (for example, `mkcert`) and terminate TLS in a local reverse proxy. Keep production CORS set to `*` only for local development; use the exact HTTPS origin in production.
