# Future roadmap — from POS to Restaurant Intelligence Platform

This is the forward-looking companion to `DOCUMENTATION.md`. It records the
long-term product vision (recipes/BOM, purchasing, an inventory ledger, a
business-event layer, forecasting, and eventually a governed AI/agent
layer), audited against **what this codebase already has today**, so
planning starts from reality instead of assumption. Every "already done"
claim below was verified by reading the actual models/services in this
repo, not inferred.

Nothing here is authorized work — it's a planning reference. Follow
`deploy/CHANGE-OWNERSHIP.md`'s change-type mapping and the normal test
gates in `DEPLOYMENT-RUNBOOK.md` when any phase below actually gets built.

## 1. The vision, condensed

```
POS  →  Restaurant Operations Platform  →  Restaurant Intelligence Platform  →  Semi-Autonomous Restaurant OS
```

The guiding principle for every phase from here on:

> **AI should never own business logic.** Stock math, accounting, taxes,
> permissions, and shift reconciliation stay deterministic application
> code. AI only interprets already-computed information and, later,
> orchestrates pre-approved actions through a narrow, permission-checked
> tool gateway — never direct database access.

## 2. Current-state audit

Item numbers match the order they were raised in. This is the single most
useful part of this document — it changes where several phases should
start.

| # | Proposed item | Status | What actually exists |
|---|---|---|---|
| 1 | Recipes/BOM (Zinger Burger → bun/chicken/cheese/mayo/packaging) | **Not built** — but a related precedent exists | `VariantOption.component_product_id` + `ProductVariantOptionGroup.usage_type="inventory_component"` (the "Laptop Store shareable-inventory model") already does *shared, separately-tracked stock pools consumed by multiple products* — the same core idea a recipe ingredient needs. It's single-select, 1-unit-per-selection, and customer/cashier-chosen, not a fixed multi-ingredient bill-of-materials auto-applied on every sale. A real `Recipe`/`RecipeIngredient` model is still needed, but it can reuse the same "ingredient is a real trackable Product+Variant" pattern instead of inventing a new stock concept. |
| 2 | Purchasing + Suppliers | **Not built** | No `Supplier`, `PurchaseOrder`, or `GoodsReceipt` model/table/route exists anywhere in the backend. Confirmed by directory listing — genuinely greenfield. |
| 3 | Inventory ledger | **Already built**, under a different name | `StockAdjustment` (`models/stock_adjustment.py`) is exactly this: `adjustment_type` (`opening`, `manual_set`, `sale`, `refund`, `transfer_in`, `transfer_out` confirmed in use today), `quantity_change`, `resulting_quantity`, branch-scoped, soft-deletable, fully audited. `VariantBranchStock.stock_quantity` is the cached running balance the proposal itself recommends keeping alongside the ledger. The only real gaps: no `purchase` or `waste` adjustment type yet (both needed once Phase 2/3 below exist), and no dedicated "Record Waste" UI action. |
| 4 | Operational Event Layer (`BusinessEvent`, `SALE_COMPLETED` etc.) | **Not built** — adjacent-but-different thing exists | `AuditLog` (`models/audit_log.py`) already captures "who did what" for admin actions (create/update/delete/login) with `action`/`module`/`entity_type`/`entity_id`. It's an **admin audit trail**, not a **domain event stream** — no `SALE_COMPLETED`/`SHIFT_OPENED`/`STOCK_RECEIVED`-style typed events, no consumer/subscriber pattern, no payload contract. A real `BusinessEvent` model is still needed as the backbone every later phase (metrics, forecasting, recommendations, agents) would read from. |
| 5 (offline) | Offline-first POS architecture | **Already built and solid** | The Flutter POS's SQLite + delta-sync-queue design (`sync_repository.dart`, drift-based local DB, quarantine/retry handling for failed syncs — see this session's work on retryable/non-retryable sync classification) already matches the target shape exactly: sell/print/shift/payment work offline, sync resumes when connectivity returns. No work needed here — just don't regress it. |
| 6 (multi-tenant) | Multi-tenant core + vertical modules | **Already built and solid** | Platform → Tenant → Business → Branch → Device → User is the real schema today. Business Templates (Fast Food vs. Laptop Business, each with its own `variants`/`addons`/`inventory`/`pricing`/`modules` config) are exactly the "core vs. vertical module" split the proposal describes — a restaurant's Recipes feature would slot in as one more template-gated vertical concept, the same way Variant Option Groups and Add-on Groups already are. |
| — | Reporting foundation | **Already built, directly reusable** | `TenantReportService`'s aggregation patterns (this session added Refunds/Cancellations, Year Comparison, and per-shift Cash Reconciliation reporting) are the same shape `DailyMetrics`/`ProductMetrics` and the Owner Assistant's "how did we do yesterday" answer would need — extend, don't replace. |
| 7 | Forecasting (moving average, exponential smoothing, day-of-week, safety stock) | **Not built** | No forecasting code anywhere. Pure-math phase, no ML framework required. |
| 8 | Recommendation Engine (`/intelligence`) | **Not built** | No such module. |
| 10-11 | AI Provider abstraction + Tool Gateway | **Not built** | No AI SDK is even a dependency yet (`requirements.txt` has none). Fully greenfield — good, because it means there's no scattered direct-provider-call debt to clean up first. |
| 12 | Owner Assistant | **Not built** | Depends on 7/8/10/11 first. |
| 13 | Approval Engine | **Not built**, one narrow precedent exists | This session's earlier work added a "superadmin password step-up" gate for deleting/changing modules on a Business Template — a single-purpose, hardcoded approval-like check, not a generic configurable `ApprovalPolicy`/`ApprovalRequest` engine. The pattern (block a sensitive action pending a second factor) is proven; the general engine still needs building. |
| 14 | Purchasing Agent | **Not built** | Depends on 1, 2, 3 (waste type), 7, 8, 13. |
| 15 | Anomaly/risk detection (void rate, refunds, discounts, cash variance) | **Not built**, but the hardest data problem is already solved | This session's Cash Shortages / shift-reconciliation feature (`CashierSessionService.list_variance()`, the `/reports/shifts` endpoint, and the tenant dashboard's Cash Shortages page) already surfaces exactly the per-cashier, per-shift variance data an anomaly detector needs as its raw signal. Void/refund/discount-rate anomaly detection is new work, but cash-variance detection is one threshold rule away from existing, real data. |
| 16 | Customer intelligence | **Not built** | No `Customer` model exists (sales aren't linked to a customer entity at all today). Correctly de-prioritized in the original notes — keep it last. |
| 18 (infra) | Redis / worker / WebSocket / Cloudflare | **Not built** | Confirmed: no `redis`, `celery`, or websocket dependency anywhere in `requirements.txt`. Today's production shape is `nginx → uvicorn (3 workers) → PostgreSQL`, nothing else — see `deploy/fastapi.service`/`deploy/nginx.conf`. A worker/queue only becomes necessary once something needs to run async or on a schedule (forecasting jobs, event fan-out at volume). |
| 20 (repo layout) | `apps/ + services/ + packages/` repo shape | **Partially already true** | The repo already has an `apps/` folder (`backend_fastfood`, `flutter_app_fastfood`, `web_fastfood`) — the target layout's top level already matches. `services/worker`, `services/intelligence`, and a shared `packages/` layer don't exist yet and shouldn't be created before something actually needs them — reorganizing a working repo ahead of need only slows product work down. |

**Bottom line:** the foundation this vision depends on — multi-tenant
core, offline POS, an audited stock ledger, a cached stock balance, and a
real reporting layer — is already in place and does not need to be
rebuilt. The genuinely new work starts at **Recipes** and **Purchasing**,
exactly where the original notes said to start.

## 3. Phased plan

Each phase lists what's new, what it reuses, the stack it needs, and a
time estimate for one developer already familiar with this codebase
(ranges, not commitments). Phases are ordered by real dependency, not just
the order they were raised — a phase never appears before something it
needs.

### Phase 1 — Recipes / Bill of Materials

**Goal:** selling 2× Zinger Burger automatically deducts 2 buns, 300 g
chicken, 2 cheese slices, 40 g mayo, 2 packaging units.

- **New models:** `Recipe` (product_id, is_active), `RecipeIngredient`
  (recipe_id, ingredient_variant_id, quantity_per_unit, unit).
- **New service:** `RecipeService` (CRUD), plus a hook inside the existing
  sale-completion path (`services/pos_sale_service.py`) that, for a
  product with an active Recipe, writes one `StockAdjustment` per
  ingredient (new `adjustment_type="recipe_consumption"`, scaled by
  `sale_item.quantity × quantity_per_unit`) alongside the sale's own
  existing stock deduction.
- **New API:** `GET/POST/PATCH /products/{id}/recipe`,
  `GET/POST/DELETE /recipes/{id}/ingredients`.
- **New web UI:** a "Recipe" tab on Product Detail (`product-detail.html`)
  — the same page this session's inventory-tracking work already lives
  in — listing ingredients with quantity/unit, add/remove rows.
- **Reuses:** `VariantBranchStock`/`StockAdjustment` as-is (an ingredient
  is just a Product+Variant like any other, the same as the existing
  "shared inventory component" precedent already treats a RAM chip);
  `TenantReportService`'s aggregation style for a later
  "ingredient consumption" report.
- **Stack:** none new.
- **Estimate:** 1.5–2 weeks (model/service/API 3–4 days, POS/dashboard UI
  4–5 days, tests 2–3 days).

### Phase 2 — Purchasing + Suppliers

**Goal:** track who supplies ingredients, at what price, and receive stock
against a purchase order.

- **New models:** `Supplier`, `SupplierItem` (supplier ↔ ingredient,
  current price), `SupplierPriceHistory` (append-only, so "chicken went
  from Rs 560→610/kg in 6 weeks" becomes a query, not a guess),
  `PurchaseOrder`, `PurchaseOrderItem`, `GoodsReceipt`, `GoodsReceiptItem`.
- **New services:** `SupplierService`, `PurchaseOrderService`,
  `GoodsReceiptService`. Receiving goods writes `StockAdjustment` with a
  new `adjustment_type="purchase"`, and appends a `SupplierPriceHistory`
  row whenever the received unit price differs from the last one.
- **New API:** `/suppliers`, `/purchase-orders`,
  `/purchase-orders/{id}/receive`.
- **New web UI:** Suppliers page, Purchase Orders list/detail, a "Receive"
  flow (mirrors the existing Devices/Branches CRUD page pattern already
  in `web_fastfood/tenant/`).
- **Reuses:** the branch/tenant scoping pattern already used everywhere
  (`api/branch_access.py`), `StockAdjustment` for the receiving side.
- **Stack:** none new.
- **Estimate:** 3–4 weeks — the largest single phase; it's a full new
  business module (header/line-items/receiving/pricing), not an extension
  of something existing.

### Phase 3 — Close the ledger gaps

**Goal:** the ledger already exists; finish it.

- Add `waste` as a first-class `adjustment_type` (Phase 1's recipe
  consumption already needed `recipe_consumption`; this adds the other
  missing type from the original proposal).
- New small feature: "Record Waste" action on the Inventory page
  (`inventory.html`), same shape as the existing Increase/Decrease/Set
  Stock actions.
- Confirm/extend the Stock Movement report (`inventory.html`'s existing
  Movement tab) to filter by the two new types.
- **Estimate:** 3–5 days — this is finishing work, not new architecture.

### Phase 4 — Operational Event Layer

**Goal:** a single, typed stream every later phase (metrics, forecasting,
recommendations, agents, notifications) can read from, instead of each
one re-deriving state from `Sale`/`StockAdjustment`/`CashierSession`
directly.

- **New model:** `BusinessEvent` (event_type, tenant_id, branch_id,
  device_id, entity_id, occurred_at, payload JSONB, indexed on
  `(tenant_id, event_type, occurred_at)`).
- **New service:** a small `emit_event(...)` helper, called from existing
  service methods at the moments listed in the original proposal
  (`SALE_COMPLETED`/`VOIDED`/`REFUNDED`, `SHIFT_OPENED`/`CLOSED`,
  `STOCK_RECEIVED`/`ADJUSTED`/`TRANSFERRED`/`WASTED`,
  `PURCHASE_CREATED`/`RECEIVED`, `EXPENSE_RECORDED`, `PRICE_CHANGED`,
  `PAYMENT_RECEIVED`).
- This is **cross-cutting instrumentation**, not a new feature — the real
  work is adding one `emit_event(...)` call to ~12–15 existing service
  methods (`pos_sale_service.py`, `cashier_session_service.py`,
  `pos_return_service.py`, the new `PurchaseOrderService`/
  `GoodsReceiptService` from Phase 2, `expense_service.py`, etc.) and
  testing that none of them regress.
- **Stack:** none new yet (a plain table is enough at this volume; revisit
  only if event volume later justifies a message bus).
- **Estimate:** 1.5–2 weeks (model+helper is quick; wiring and testing
  ~15 call sites carefully is the real time cost).

### Phase 5 — Deterministic analytics + forecasting (no AI)

**Goal:** "Chicken: 18 kg on hand, 12.8 kg/day average use, 1.4 days
remaining" — pure math, computed from `BusinessEvent`/`StockAdjustment`.

- **New models:** `DailyMetrics`, `ProductMetrics` (precomputed daily
  rollups per branch/product — revenue, quantity sold, consumption rate).
- **New service:** forecasting math — moving average, exponential
  smoothing, day-of-week averages, safety-stock calculation. Hand-rolled
  Python is enough at this stage; no ML framework needed.
- **First new infra decision:** these rollups need to run on a schedule.
  Cheapest option: `APScheduler` inside the existing FastAPI process (zero
  new infra, fine at current scale). Heavier option: a real worker
  (Celery/RQ + Redis) — defer until Phase 4's event volume or Phase 6's
  recommendation frequency actually needs it.
- **Estimate:** 2–3 weeks.

### Phase 6 — Recommendation Engine

**Goal:** `{"type": "LOW_STOCK", "item_id": "chicken", "recommended_quantity": 40, ...}`,
surfaced as a dashboard card with a one-click "Create Purchase Order."

- **New models:** `Recommendation`, `RecommendationAction` (accepted /
  ignored / modified, for later measurement of recommendation quality).
- **New domain:** `services/intelligence/` (or `api/v1/intelligence.py` +
  a matching service) — reads `ProductMetrics`/forecast output +
  current `VariantBranchStock`, writes `Recommendation` rows.
- **New API:** `GET /intelligence/recommendations`.
- **New web UI:** recommendation cards wired to Phase 2's
  "Create Purchase Order" flow.
- **Estimate:** 2 weeks.

### Phase 7 — Approval Engine

**Goal:** thresholds like "Purchase ≤ Rs 5,000 → Manager approves;
Rs 5,001–25,000 → Owner; > Rs 25,000 → Owner + admin" — must exist
**before** anything downstream gets to act on its own.

- **New models:** `ApprovalPolicy`, `ApprovalRequest`, `ApprovalAction`,
  `ApprovalAuditLog`.
- **New service:** `ApprovalService`, generic enough to gate any future
  write action (a purchase order, later an agent-suggested action) behind
  a configured threshold.
- **New web UI:** policy configuration (Owner/Admin only, matching the
  existing tenant-admin permission pattern) + an approval inbox.
- **Reuses:** the step-up-authentication precedent from the Business
  Template module-change gate mentioned in the audit above.
- **Estimate:** 1.5–2 weeks.

### Phase 8 — AI Provider abstraction + Tool Gateway

**Goal:** one internal interface, swappable providers, and AI that can
only call named, permission-checked functions — never raw SQL.

- **New module:** `core/ai/provider.py` — an abstract `AIProvider` with
  `summarize`/`classify`/`reason`/`extract`, plus adapters
  (`AnthropicProvider`, `OpenAIProvider`, ...). Every call in the
  application goes through this interface, never a provider SDK directly.
- **New module:** `core/ai/tools.py` — the Tool Gateway. Each tool is a
  plain Python function with an explicit permission check, wrapping an
  **existing** service call (`get_sales_summary` → `TenantReportService`,
  `get_stock_status` → `VariantService`, `get_cash_variances` →
  `CashierSessionService.list_variance()` — already built this session,
  `get_shift_summary`, `get_expenses`, `get_waste_report`, and exactly one
  write tool, `create_purchase_order_draft`, which must route through
  Phase 7's `ApprovalService` before it can do anything).
- **Stack:** the chosen provider's Python SDK (e.g. `anthropic`), new
  `.env` vars for the API key — nothing else.
- **Estimate:** 2 weeks for the abstraction plus the first ~8–10 read
  tools and the one gated write tool.

### Phase 9 — Owner Assistant

**Goal:** "How did my restaurants perform yesterday?" answered with real
numbers, in plain language, generated *from* Phase 8's tools — the
assistant never computes a number itself.

- **New API:** `POST /assistant/ask`.
- **New web UI:** a chat-style panel in the tenant dashboard.
- **Estimate:** 2 weeks — mostly tool coverage and prompt/response
  formatting, not new backend logic.

### Phase 10 — First real agent: Purchasing Agent

**Goal:** forecast → check stock-out date → check supplier/price →
draft a PO → route through approval → send.

- **New models:** `AgentAction`, `AgentRun`, `AgentAuditLog` — full
  traceability of every suggestion an agent ever makes.
- Wires together Phases 2, 5, 6, 7, and optionally 8 (the AI layer is
  genuinely optional here — the whole pipeline the original notes
  describe is deterministic except the final explanation text).
- **Estimate:** 1.5–2 weeks — mostly integration of already-built pieces.

### Phase 11 — Anomaly / risk detection

**Goal:** unusual void rate, refund rate, discount frequency, and cash
variance, surfaced for human review — never an automatic accusation.

- **New model:** `Anomaly`.
- **New service:** threshold/rate-based rules (z-score or simple
  percentage-over-baseline) reading `BusinessEvent` — no ML needed.
- **Head start:** cash-variance detection can be built almost immediately
  on top of the existing `/reports/shifts` data (this session's Cash
  Shortages feature) — it's a threshold rule away from working today,
  independent of Phase 4's event layer.
- **Estimate:** 1.5–2 weeks.

### Phase 12 — Customer intelligence

**Goal:** segmentation, churn signals, loyalty — deliberately last, as the
original notes themselves recommend.

- **New model:** `Customer`, plus linking `Sale` to a customer
  (currently sales carry no customer reference at all).
- **Estimate:** 2–3 weeks, whenever it's prioritized.

## 4. Data model additions — master list

| Model | Status |
|---|---|
| `Supplier`, `SupplierItem`, `SupplierPriceHistory` | New (Phase 2) |
| `PurchaseOrder`, `PurchaseOrderItem` | New (Phase 2) |
| `GoodsReceipt`, `GoodsReceiptItem` | New (Phase 2) |
| `Recipe`, `RecipeIngredient` | New (Phase 1) |
| Inventory ledger | **Already exists** — `StockAdjustment` |
| Cached stock balance | **Already exists** — `VariantBranchStock` |
| `BusinessEvent` | New (Phase 4) |
| `DailyMetrics`, `ProductMetrics` | New (Phase 5) |
| `Recommendation`, `RecommendationAction` | New (Phase 6) |
| `ApprovalPolicy`, `ApprovalRequest`, `ApprovalAction`, `ApprovalAuditLog` | New (Phase 7) |
| `AgentAction`, `AgentRun`, `AgentAuditLog` | New (Phase 10) |
| `Forecast` | New (Phase 5, may fold into `ProductMetrics` rather than its own table) |
| `Anomaly` | New (Phase 11) |
| `Notification` | New — not yet scoped to a single phase; needed once Phase 6/11 need to push something to a human instead of waiting for them to look |
| `Customer` | New (Phase 12) |

## 5. Infra evolution

Today: `Cloudflare (optional, ops-only) → nginx → uvicorn (3 workers) →
PostgreSQL`. No Redis, no worker, no WebSocket layer.

- **Cloudflare in front of nginx** is a pure ops change (DNS + proxy
  config) — can happen anytime, independent of any phase above, and isn't
  blocked by or blocking any of them.
- **A worker + Redis** only becomes necessary once Phase 5's scheduled
  rollups or Phase 4's event volume actually need async/background
  processing at a scale `APScheduler`-in-process can't handle. Don't add
  this infra ahead of that need.
- **WebSocket** isn't required by anything in this roadmap as written —
  the Owner Assistant (Phase 9) and recommendation cards (Phase 6) are
  fine as ordinary request/response; only add it if a real-time push
  requirement shows up later.

## 6. Realistic timeline

Summing the phase estimates above (Phases 1–12; Phase 0's foundation is
already done):

- **~24–28 weeks (roughly 5.5–7 months) sequential, one developer.**
- Meaningfully shorter with 2–3 developers working phases in parallel
  where dependencies allow — for example, Phase 1 (Recipes) and Phase 4
  (Event Layer) don't depend on each other and can run side by side;
  Phase 12 (Customer Intelligence) can be deferred or parallelized
  independently at any point after Phase 0 without blocking anything else.
- The two phases worth treating as genuinely load-bearing for everything
  after them are **Phase 2 (Purchasing)** and **Phase 4 (Event Layer)** —
  most later phases either consume purchasing data or subscribe to the
  event stream. Prioritize those two once Phase 1 (Recipes) is done.
