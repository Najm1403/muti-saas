# Creating promotions and deals

This guide covers the tenant dashboard workflow and the resulting POS behavior.
Promotions and deals are tenant-scoped, may be restricted to branches, and are
revalidated by the backend when a sale is completed.

## Promotion or deal?

| Feature | Best use | Examples |
| --- | --- | --- |
| **Promotion** | A cart discount or reward that becomes eligible after conditions are met; it may be automatic or require a code | 10% off, Rs. 500 off Rs. 5,000, buy two and get one free |
| **Deal / Combo** | A defined bundle containing required product or category quantities and one bundle price/discount | Laptop + bag for Rs. 100,000, burger + drink combo |

Only one promotion or deal may be applied to an order. A manual discount is a separate
workflow and requires `sales.discount`; it must not be combined with an applied offer.

## Before creating an offer

1. In the platform configuration, make sure the tenant has the **Promotions** and/or
   **Deals / Combos** module enabled. Disabled modules are neither manageable in the
   tenant dashboard nor evaluated by the POS.
2. Use a tenant user with `products.view` to view offers and `products.manage` to
   create, edit, assign branches, or delete them.
3. Create and activate all referenced products/categories first. Each sellable reward
   product needs a default Variant; required Variant selections cannot be automatically
   chosen for a free reward.
4. Decide the eligible branches, validity dates, and pricing before activating the
   offer.

The current forms accept product and category UUIDs. To find them, open **Menu**, open
the relevant product detail page, and copy `product_id` or `category_id` from its browser
address, for example:

```text
/tenant/menu/product-detail.html?product_id=PRODUCT_UUID&category_id=CATEGORY_UUID
```

Copy only the UUID value, not the parameter name or `&` separator. Use a Product ID or
a Category ID in a target field unless the offer intentionally needs both conditions.

## Create a percentage or flat-amount promotion

1. In the tenant dashboard, open **Promotions** and select **Add Promotion**.
2. Enter a clear **Name** and optional **Description**.
3. Choose **Percentage Discount** or **Flat Amount Off**.
4. For **Promo Code**:
   - leave it blank to make the promotion appear automatically whenever its conditions
     match;
   - enter a unique code to require the cashier to type that code. The dashboard saves
     it in uppercase, so use the exact uppercase code at the POS.
5. Enter **Discount Value**. Percentage values should normally be from `0` to `100`;
   flat discounts are capped at the order subtotal by the server.
6. Add optional trigger conditions:
   - **Min Quantity** is the minimum matching item quantity;
   - **Min Order Amount** is the minimum cart subtotal;
   - **Trigger Product ID** requires that product;
   - **Trigger Category ID** requires a product in that category.
7. Set **Valid From** and **Valid Until** if the offer is time-limited. Blank dates mean
   no boundary on that side.
8. Set **Max Uses** to limit completed uses, or leave it blank for unlimited use.
9. Leave **Active** selected only when the offer is ready.
10. Under **Branch Availability**, keep **all branches** selected or clear it and select
    the permitted branches.
11. Select **Save**.

Trigger product/category fields qualify the promotion; percentage and flat discounts
are calculated against the order subtotal. For example, a `10%` promotion triggered by
one RAM product discounts 10% of the qualifying cart's subtotal, not only the RAM line.

### Example: automatic 10% discount above Rs. 5,000

- Type: **Percentage Discount**
- Promo Code: blank
- Discount Value: `10`
- Min Order Amount: `5000`
- Active: selected
- Branches: choose the intended branches

### Example: code-based Rs. 500 discount

- Type: **Flat Amount Off**
- Promo Code: `SAVE500`
- Discount Value: `500`
- Optional Min Order Amount: for example `5000`

## Create Buy X Get Y or Free Item promotion

1. Open **Promotions > Add Promotion**.
2. Choose **Buy X Get Y** or **Free Item**.
3. Define what the customer must buy under **Trigger Conditions**:
   - set a Trigger Product or Category;
   - set **Min Quantity** to X;
   - optionally set a minimum cart amount.
4. Under **Reward**, set **Reward Quantity** to Y.
5. Set exactly one reward target: **Reward Product ID** or **Reward Category ID**. The
   API rejects a BXGY/FREE_ITEM promotion without a reward target.
6. Select the reward discount:
   - **100% Free** gives the full reward value free;
   - **Percentage** applies that percentage to the reward value;
   - **Flat Amount** deducts up to the entered amount from the reward value.
7. Set the promo code, validity, maximum uses, active state, and branches as required,
   then save.

When a qualifying reward can be added automatically, POS preview adds a separate reward
line using its default Variant. At final checkout the server verifies that the reward
line and required quantity are actually present. For a reward category, eligibility is
resolved from active products in that category; test the exact product chosen before
publishing the offer. If the reward product requires the cashier to choose mandatory
Variant options, automatic reward insertion is skipped, so use a reward product with an
unambiguous default Variant.

### Example: buy two RAM modules, get one specified item free

- Type: **Buy X Get Y**
- Trigger Product ID: the RAM product UUID
- Min Quantity: `2`
- Reward Product ID: the free item's product UUID
- Reward Quantity: `1`
- Reward Discount Type: **100% Free**

## Create a deal or combo

A deal has two stages: first create its header/pricing, then add every required bundle
item.

### Stage 1: create the deal

1. In the tenant dashboard, open **Deals** and select **New Deal**.
2. Enter **Name**, a unique **Deal Code** of 2-50 characters, and an optional
   description.
3. Choose one pricing approach:
   - **Fixed Price** sets the price of the complete matched bundle. It overrides the
     ordinary sum of product prices for offer calculation.
   - Or leave Fixed Price blank and choose **Flat Amount** or **Percentage**, then enter
     **Discount Value**.
4. Set validity dates if required.
5. Set **Display Order**; lower numbers are listed first in management/POS data.
6. Select **Active** only when the deal is ready for use.
7. Choose all branches or specific branches, then select **Save**.

Do not configure both Fixed Price and a discount expecting both to apply. Fixed Price
takes precedence. With percentage/flat pricing, deal items marked **Free item** are
discounted fully and the configured percentage/flat discount applies to the remaining
bundle value.

### Stage 2: add required deal items

1. Select the saved deal from the left-hand list.
2. Under **Deal Items**, select **Add Item**.
3. Enter either a **Product ID** for one exact product or a **Category ID** to allow a
   matching product from that category.
4. Set **Quantity** to the number required in one bundle.
5. Set **Sort Order** to control line order.
6. Select **Free item** only if that slot must be fully free under percentage/flat deal
   pricing.
7. Select **Add** and repeat until the complete bundle is represented.
8. Review the item table and branch availability. Remove and recreate an incorrect item
   if necessary.

An eligible cart must satisfy every deal-item slot and quantity. Category slots consume
matching cart products, and one cart unit cannot satisfy two required slots. The deal
discount is limited to the calculated value of the matched bundle.

### Example: laptop and bag for a fixed price

- Deal name: `Laptop Starter Bundle`
- Deal code: `LAPTOP-BAG`
- Fixed Price: the intended bundle price
- Item 1: Laptop Product ID, Quantity `1`
- Item 2: Bag Product ID, Quantity `1`
- Free item: not selected, because Fixed Price controls the complete bundle price

## Make an offer available at the POS

1. Save the offer with **Active** selected and confirm the current date/time is inside
   its validity window.
2. Confirm the POS branch is included in **Branch Availability**.
3. On each POS, use **Settings > Sync now**, or wait for the automatic sync. Deals and
   promotions are included in full and delta catalog sync.
4. Add the qualifying products and quantities to the cart.
5. Open the cart and select **Offers and deals**.
6. Enter the promo code when the promotion is code-gated, or leave it blank to find
   automatic promotions and eligible deals.
7. Select **Find offers**, inspect the calculated discount, and select the desired
   offer. Only one can be applied.
8. If the cart changes afterward, find and apply the offer again.
9. Complete payment while online. The backend recalculates eligibility, amount, branch,
   dates, remaining usage, and cart contents. If anything changed, the POS asks the
   cashier to reapply the offer.

Applied promotion/deal IDs and the final discount are stored with the sale for audit.
A promotion's use count increases only when an eligible sale is committed, not when an
offer is merely previewed.

## Edit, disable, and delete safely

- Clear **Active** to stop new uses without deleting historical configuration. Sync the
  POS afterward.
- Existing sales retain their applied offer reference and monetary snapshots.
- For a promotion, ordinary fields such as name, code, discount, thresholds, dates,
  maximum uses, and active state can be edited. The promotion type and product/category
  target structure are creation-time fields in the current API; recreate the promotion
  if those must change.
- A deal code is creation-time in the current API. Other deal pricing/display fields can
  be edited; add or remove bundle items from its detail panel.
- **Delete** performs a soft delete and removes the offer from new evaluation. Prefer
  deactivation for temporary campaigns and deletion for incorrect/obsolete records.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Promotions/Deals page is unavailable | Enable the matching tenant module and verify user permissions |
| Offer does not appear after saving | Active state, dates/time zone, branch assignment, POS sync, trigger quantities and minimum amount |
| Code promotion does not appear | Enter the exact saved uppercase code; codes are unique per tenant |
| Deal does not appear | Every required product/category slot and quantity must be in the cart |
| Reward is not added | Reward target must exist, be active, have a default Variant, and not require unresolved mandatory selections |
| Offer disappeared at checkout | The server revalidation found a changed cart, expired/disabled offer, exhausted Max Uses, wrong branch, or changed price/eligibility; sync and reapply |
| Discount is larger than expected | Percentage/flat promotions discount the order subtotal after their trigger qualifies; review the intended design |
| Product/category field is rejected | Copy only a valid UUID belonging to the same tenant |

## Acceptance checklist

1. Test automatic and code-gated promotions at an included and excluded branch.
2. Test just below and exactly at minimum quantity/amount boundaries.
3. Test the start/end time and Max Uses boundary.
4. Test each reward type and verify the receipt, stock deduction, and sale audit.
5. Test a fixed-price deal and a percentage/flat deal with a free item.
6. Change the cart after applying an offer and confirm the POS requires reapplication.
7. Disable the offer, sync the POS, and confirm no new sale can apply it.
8. Return an offered sale and confirm the refund uses the original discounted sale
   values, following [POS bill cancellation and sales returns](POS_RETURNS_AND_CANCELLATIONS.md).
