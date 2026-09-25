# Sales and reporting

This document is the operating and testing reference for sales history and reports in
the tenant dashboard and the Windows/Android POS. The cloud PostgreSQL database is the
authoritative long-term record. The POS keeps a bounded SQLite copy so recent work can
still be reviewed during a temporary network outage.

## Business rules

- A sale carries the cashier `user_id` and the active shift `session_id`. The supported
  POS client sends both when checkout is completed. The backend validates a supplied
  shift against the authenticated cashier, device, branch, and tenant.
- The backend retains a compatibility fallback for an older or manually integrated
  client that omits `session_id`: it tries to match the cashier's open session by
  device and time. New clients must not rely on this fallback.
- Date, branch, cashier, and shift filters are cumulative (logical AND). A user can
  report only on branches allowed by that user's branch scope.
- Completed sales contribute to revenue. Cancelled bills remain visible for audit but
  do not count as completed revenue. Returns/refunds remain linked to the original
  invoice and are reconciled separately.
- Display the human sale number and cashier name in the UI. UUID values remain internal
  identifiers for synchronization, joins, and API operations.

## Tenant dashboard

The **Sales** page can filter by branch, inclusive date range, status, cashier, and
shift. It calls:

```text
GET /api/v1/sales/?branch_id=<uuid>&date_from=<UTC>&date_to=<UTC>
    &status=<COMPLETED|CANCELLED|REFUNDED>&user_id=<uuid>&session_id=<uuid>
```

The **Reports** page has two tabs: **Sales Report** and **Year Comparison** (see below).
The Sales Report tab applies its selected branch/date/cashier/shift scope consistently
to summary, refunds, payment-method, product, cashier, and branch panels, and switches
its trend chart between daily and monthly based on the selected range (see "Report
granularity" below) rather than showing both at once. The report endpoints are:

```text
GET /api/v1/reports/summary
GET /api/v1/reports/daily
GET /api/v1/reports/monthly
GET /api/v1/reports/products
GET /api/v1/reports/cashiers
GET /api/v1/reports/branches
GET /api/v1/reports/payment-methods
GET /api/v1/reports/refunds
GET /api/v1/reports/returned-products
GET /api/v1/reports/year-comparison
GET /api/v1/reports/year-comparison/pdf
GET /api/v1/reports/shifts
GET /api/v1/reports/pdf
GET /api/v1/reports/yearly
```

Use ISO-8601 UTC datetimes for API calls. The browser converts a selected calendar day
to the correct start/end instants so the complete local day is included.

### Report granularity

`reports.html`'s `computeGranularity()` decides which trend chart applies to the
selected date range, so Today/Week/Month never pull in a Quarter's or Year's worth of
unrelated data and vice versa: a range of 31 days or less shows the **Daily** chart
(`GET /reports/daily`); a longer range shows the **Monthly** chart (`GET /reports/monthly`),
scoped to the range's own year and, when the range stays inside one calendar year, its
month span too. No date range at all ("All time") defaults to monthly. The same rule is
mirrored server-side in `api/v1/reports.py::_report_granularity()` so `GET /reports/pdf`
never mixes the two either. `GET /reports/yearly` (the older all-time year trend) still
exists for API compatibility but is no longer shown on this tab — see **Year Comparison**
below for the current year-over-year view.

### Refunds & Cancellations reporting

The Sales Report tab's "Refunds & Cancellations" section (auto-hidden when there's no
refund activity in the selected period) shows KPI tiles (Returns, Cancellations, Total
Refunded, Refunded Sales), a per-payment-method breakdown for each, and a "Top Returned /
Cancelled Products" table — sourced from `TenantReportService.get_refunds_summary()` and
`get_returned_products()`. `RETURN` (a later, possibly partial item return) and `CANCEL`
(a same-shift full reversal) are tracked and reported separately throughout. The Summary
Cards section also surfaces `refunded_sales`/`refund_total`/`cancellation_total` directly
on `SalesSummary`, not just the bare `cancelled_sales` count.

### Year Comparison tab

A dedicated tab for comparing full years side by side — deliberately separate from the
Sales Report tab's own date-range filter, since "compare 2023 to 2026" isn't a single
contiguous range. Pick years via toggle chips (up to 8 at once) or the "Last 5 Years"
shortcut; results are a KPI headline for the most recent selected year (including YoY
growth %, `None` rather than a nonsensical value when there's no prior-year data), a
year-by-year summary table, a multi-line monthly-revenue chart (one line per year, using
the dataviz skill's validated categorical palette in fixed order), and a month × year
revenue matrix — plus its own PDF export (`GET /reports/year-comparison/pdf`). Backed by
`TenantReportService.get_year_comparison()`, which always fetches the immediately
preceding calendar year too (even if not itself selected) so growth % is real even for a
non-contiguous comparison.

### Cash Shortages page (shift cash reconciliation)

`apps/web_fastfood/tenant/shifts.html` (`GET /api/v1/reports/shifts`) — previously, a
shift's cash variance (closing cash counted vs. expected cash from opening cash + cash
sales − cash refunds) was visible only to the cashier who closed it, on their own device,
recomputed live and never stored anywhere else. This page gives tenant admins the same
reconciliation, branch-scoped, with a "Shortages only" filter, backed by
`CashierSessionService.list_variance()` (which reuses the same `_summary()` the cashier's
own close-shift screen already uses — the money math can't drift between the two views).
Each row shows the shift's human-readable **shift number**: `YYMMDD` + the device's
permanent letter (e.g. `A`, `B`, per branch) + that device's Nth shift opened that day —
e.g. `260924A1`, then `260924A2` for its second shift the same day. Computed once at
`CashierSessionService.open()` and stored on `CashierSession.shift_number`; `None` for
shifts opened before this field existed.

## POS recent sales and reports

After an online sale is confirmed, the POS writes the confirmed receipt to SQLite.
An offline sale is written to the same local tables as an unsynced row and uploaded
when connectivity returns. The Reports screen merges cloud receipts with local rows,
deduplicates them by sale number, and supports date, cashier, and shift filters.

Important boundaries:

- `GET /api/v1/pos/sales/recent` is scoped by the authenticated cashier, device,
  branch, and tenant. It accepts `date_from`, `date_to`, `session_id`, and a maximum
  `limit` of 200.
- The POS report can render up to 1,000 retained local/merged rows. This is an
  operational recent-history view, not a replacement for the tenant's cloud reports.
- Synced local sales older than 90 days are eligible for cleanup. Cleanup runs after a
  successful online sale, so an idle installation may keep old rows until its next
  confirmed checkout.
- Unsynced rows are never removed by retention cleanup.
- SQLite schema version 13 adds local cashier ID and sale status. The Drift migration
  runs automatically when an existing POS installation starts; no manual SQLite
  command is required.
- A successful cancellation updates the cached local sale status. Cloud reports remain
  authoritative for detailed return/refund reconciliation.

## Manual acceptance test

1. Sign in as Cashier A, open Shift A, and complete two sales. Confirm the receipt and
   Sales page show the human invoice number and Cashier A's name, not UUIDs.
2. Close Shift A, open Shift B, and complete another sale. In tenant **Sales**, filter
   by Cashier A and then each shift. Confirm only matching invoices appear.
3. In tenant **Reports**, use the same dates, cashier, and shift. Confirm every
   date-range panel changes to that scope; confirm monthly/yearly use the same cashier
   and shift, and that monthly loads without a PostgreSQL grouping error.
4. Open POS **Reports** while online. Confirm recent cloud and local receipts are not
   duplicated. Apply date, cashier, and shift filters.
5. Disconnect the network, restart the POS, and repeat the local report filters. The
   retained receipts must remain readable.
6. Complete an offline sale, confirm it is shown as queued, reconnect, use **Sync now**,
   and confirm it uploads once and remains a single report row.
7. Cancel an eligible same-shift bill and confirm its local status and tenant Sales
   status are `CANCELLED`; confirm it is excluded from completed revenue.
8. In tenant **Reports**, switch the Quick Range between Today/Week/Month/Quarter/Year
   and confirm the trend chart swaps between Daily and Monthly as described under
   "Report granularity" above — never showing both, never showing an unrelated period.
9. Process a return and a same-shift cancellation. Confirm the "Refunds & Cancellations"
   section appears with correct KPI tiles and payment-method breakdowns, and that the
   Summary Cards' refunded/cancelled figures include the dollar amounts, not just counts.
10. Open the **Year Comparison** tab, confirm it defaults to the last 5 years, and that
    picking a year with no prior-year data shows "No prior-year data" rather than a
    growth percentage. Export its PDF.
11. Close a shift with `closing_cash` less than expected. Confirm the resulting shift
    appears on the tenant dashboard's **Cash Shortages** page (`shifts.html`) with a
    "Short by ..." variance, a shift number in `YYMMDD<letter><n>` form, and that the
    "Shortages only" filter still shows it.

## Automated checks

From `D:\muti-saas\apps\backend_fastfood` in PowerShell:

```powershell
$env:DEBUG='false'
python -m pytest tests/test_report_branch_integrity.py -q
python -m pytest tests/test_refunds_report.py tests/test_year_comparison_report.py tests/test_shift_variance.py -q
python -m pytest -q
```

The report regression suite must run against PostgreSQL. In particular, monthly
grouping must use the same SQL expression in `SELECT`, `GROUP BY`, and `ORDER BY`;
recreating separately parameterized expressions can fail on PostgreSQL even if a
simpler test database accepts it.

From `D:\muti-saas\apps\flutter_app_fastfood`:

```powershell
flutter test test/local_sales_reporting_test.dart
flutter test
flutter analyze
```

The focused Flutter test covers combined local filters and verifies that the 90-day
cleanup removes old synced rows without deleting an unsynced sale.
