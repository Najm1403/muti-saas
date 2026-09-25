# Variant and branch inventory

The `variants` table is authoritative for sellable SKU identity. `VariantBranchStock`
stores each Variant's integer balance per branch, while `StockAdjustment` records every
opening, manual, sale, transfer, cancellation, and eligible return movement.

## Catalog behavior

- Add Product is the only place where a product's Colors are chosen. Each selected
  color requires its own sale price and opening stock and creates a sellable Variant.
- Colors cannot be added or removed on product detail. Existing color Variant prices
  remain editable there.
- Product detail stock is read-only. **Overall Stock** shows the total across active
  branches and, for a colored product, each color's total and per-branch quantities.
- A product without colors uses its default Variant and shows overall/per-branch stock.
- **Variant Selections** are shared inventory-component choices. They do not generate
  product/color combinations or replace the product's own stock.
- Add-ons remain separate price deltas and never create stock Variants.

Inventory eligibility is:

```text
Product.allow_inventory_tracking AND Variant.tracks_inventory
```

Opening stock is recorded per branch when the Variant is created. All later Increase,
Decrease, Set Stock, Transfer, and History actions belong to Inventory and write audited
stock adjustments. Business Templates may default products to trackable, but users can
change the allowed tracking fields when the template policy permits it.

### Turning tracking on or off for an existing product

Toggling `allow_inventory_tracking` on an **existing** product (the "This product is
trackable" checkbox in Menu's Edit Product drawer) keeps every one of its Variants in
sync automatically, in both directions:

- **Turning it on** hands the admin off to Product Detail
  (`?prompt_tracking=1`), where a single combined modal lists every currently-untracked
  Variant × every assigned branch in one grid — one opening-stock entry for the whole
  product, not one per Variant. Submitting loops `PATCH /variants/{id}` once per
  Variant (`VariantService.set_tracking()`, unchanged), sequentially, so a partial
  failure is reportable instead of all-or-nothing.
- **Turning it off** (`ProductService.update()`) bulk-sets every currently-tracked
  Variant's `tracks_inventory` back to `False` in the same transaction. Existing
  `VariantBranchStock`/`StockAdjustment` rows are left alone — this only stops
  enforcement going forward, it never erases history. Before this cascade existed, a
  Variant left at `tracks_inventory=True` while its product was untracked was silently
  orphaned: every stock check ANDs both flags, so it just stopped being enforced with
  no visible signal, and "Enable tracking" would never re-offer it since the column
  already read `True`.

This only applies to editing an existing product. **Creating** a product already
cascades `allow_inventory_tracking` into its auto-seeded default Variant (and any
create-time priced Color Variants) and collects opening stock inline in the same form —
see `ProductService.create()`.

## API and dashboard

Inventory reads from `GET /api/v1/variants?tracked_only=true`. Stock operations use:

```text
GET  /api/v1/variants/{id}/stock
POST /api/v1/variants/{id}/stock
POST /api/v1/variants/{id}/stock/increase
POST /api/v1/variants/{id}/stock/decrease
POST /api/v1/variants/{id}/transfer
GET  /api/v1/variants/{id}/history
```

The Inventory page searches product, color/Variant display name, and Variant ID. Its
in-stock, out-of-stock, and low-stock filters use the selected branch balance. Restricted
users receive only assigned-branch rows, and transfers require access to both branches.
Low-stock notifications and filters apply only to Variants eligible for tracking and
use the Business-wide threshold configured in tenant Settings.

## Sales and integrity

Sales aggregate demand by Variant, lock the branch-stock row, reject disallowed negative
stock, and write the sale and stock movements atomically. Cancellation and return logic
restores only quantity actually deducted at sale time and still eligible under the current
tracking gates. A partial return cannot restore more than the remaining sold quantity.

The history API exposes `change_type`, nullable `quantity_delta` (`null` for
`manual_set`), `resulting_quantity`, reference, actor, and timestamps. Opening stock is
derived from its opening adjustment, never from today's balance.

## Deployment and verification

1. Upload pending offline sales and back up PostgreSQL.
2. From `apps/backend_fastfood`, run `python -m alembic upgrade head` and restart the API.
3. Deploy updated POS clients and run a full catalog sync.
4. Create a plain product and a colored product. Verify create-time price/opening stock,
   read-only product-detail totals, Inventory actions/history, branch filters, and low
   stock behavior.
5. Sell, cancel, and partially return tracked items. Confirm only the affected branch and
   Variant change and every movement has an audit record.

Roll back application releases and migrations as one reviewed operation, then run a full
catalog sync on every POS. The Variant routes above are the supported inventory contract.
