# POS bill cancellation and sales returns

This guide explains the two financial-reversal workflows available in the Windows
and Android POS clients. They are deliberately separate because they represent
different business events and have different controls.

## Choose the correct operation

| Operation | Use it when | Scope | Time and ownership rule | Final sale status |
| --- | --- | --- | --- | --- |
| **Cancel Order / Bill** | The cashier completed a bill by mistake and must immediately reverse it | The complete invoice only | Same cashier, same device, and the same still-open shift | `CANCELLED` |
| **Sales Return** | A customer brings back one or more items from a completed invoice | Selected items and quantities | May be performed in a later shift, but only at the sale's branch | `COMPLETED` after a partial return; `REFUNDED` after all remaining items are returned |

Do not use cancellation for a customer return. Do not use a partial return to
correct a just-created mistake bill when the whole bill should be reversed.

## Prerequisites and controls

Before either operation:

1. The backend must be reachable. Reversals are online-only because the server locks
   the sale and checks its current status, previous returns, quantities, payment
   allocation, and stock before committing one transaction.
2. The cashier must be signed in and have an open shift on the activated device.
3. The cashier's role must include `sales.cancel`. A tenant administrator grants this
   permission through role management; removing it prevents both cancellation and
   return submission.
4. The invoice must belong to the device's branch. Cross-branch lookup or reversal is
   not allowed.
5. The sale must be fully synchronized. A locally queued sale cannot be reversed until
   it has uploaded successfully and can be found by its printed Invoice ID.

The server, not the POS screen, calculates every reversal amount. The client sends
only the invoice, selected lines and quantities, and the reason. This prevents a
cashier from changing the historical sale price or inventing a refund amount.

## Cancel a mistaken bill

Cancellation is a complete reversal. Individual lines cannot be selected.

### From the completed receipt

1. Complete the sale normally.
2. On the completed receipt, select **Cancel Order / Bill**.
3. Enter a meaningful reason, such as `Duplicate bill` or `Wrong payment completed`.
   A reason is mandatory and is limited to 500 characters.
4. Review the confirmation and submit it once.
5. Confirm that the POS reports success and that the bill is marked `CANCELLED`.

### From Recent transactions

1. Return to the POS dashboard and open **Recent transactions**.
2. Open the mistaken invoice.
3. Select **Cancel Order / Bill**, enter the required reason, and confirm.

The cancellation button is useful only while the original cashier's shift is still
open on the original device. If that shift has closed, use **Sales Return** instead.

### What cancellation records

The backend creates a completed refund audit record with:

- type `CANCEL` and a unique `CAN-...` reference;
- the complete set of original sale lines and quantities;
- the server-calculated full remaining amount;
- the original payment-method allocation, including split payments;
- the reason, processing cashier, current shift, branch, device, and timestamps.

The original sale is retained for audit and changes to `CANCELLED`; it is never erased.
Any inventory that was actually deducted from tracked Variants is restored at the
original branch. Untracked lines are not changed. A cancellation cannot be repeated
and cannot be made after any return already exists for the bill.

## Return items from an invoice

Sales Return supports one line, several lines, or every remaining line from an old
bill. A return may be processed during a later open shift.

1. From the main POS dashboard, open **Sales Return**.
2. Enter the exact printed **Invoice ID**. Use the human-readable invoice number from
   the receipt, not a database UUID.
3. Select **Find invoice** and verify the customer bill, items, quantities, and totals.
4. For each item physically returned, select it and enter the quantity. The quantity
   cannot exceed the purchased quantity minus quantities already returned.
5. Enter a useful return reason. It is stored in the audit record.
6. Review the calculated amount and confirm the return.
7. Give the customer the amount shown using the original payment allocation. For a
   split-payment sale, the return is allocated across the still-refundable original
   payment methods rather than being assigned to a new arbitrary method.

The price basis is the immutable original sale line. Proportional order-level
discounts are preserved in the calculated refund. Current catalog prices and later
price changes do not alter the amount.

After a partial return, the sale remains `COMPLETED` so its other lines remain
returnable. Once every purchased unit has been returned and the full paid total has
been accounted for, the sale changes to `REFUNDED`. Each return gets its own completed
`RETURN` audit record and `RET-...` reference.

## Inventory, payments, shifts, and reports

- Stock restoration is branch-specific and Variant-specific. Only lines recorded as
  tracked when sold are candidates for restoration, and both current inventory
  tracking switches must still permit tracking.
- A partial return restores only the selected quantity. Several returns cannot restore
  more units than were sold.
- A Free Guest order has no paid amount and cannot produce a cash refund.
- Same-shift cancellations and sales returns are separate figures in shift close,
  shift history, and generated shift PDFs. A cancelled bill is not also counted as a
  normal return.
- The refund audit identifies the processing cashier and shift, even when those differ
  from the cashier and shift that made an older sale.
- Cancellation and return records remain attached to the original invoice for tenant
  dashboard reporting and reconciliation.
- Tenant Sales and Reports can combine date, branch, cashier, and shift filters. Use
  those filters to reconcile the original sale, cancellation/return audit, and shift;
  see [Sales and reporting](SALES_AND_REPORTING.md).

## Rejections and corrective action

| Message or condition | Meaning | Action |
| --- | --- | --- |
| Permission denied / `sales.cancel` required | The role cannot perform reversals | Grant `sales.cancel` to an appropriate supervisor/cashier role, then sign in again |
| Open a cashier shift | There is no active shift for this cashier/device | Open a shift before retrying |
| Only the cashier and device that made this bill can cancel it | Cancellation ownership does not match | Let the original cashier cancel it on the original device, or use Sales Return |
| Bill belongs to an earlier shift | Cancellation window has ended | Use Sales Return |
| Sale not found in this branch | Wrong Invoice ID, unsynchronized sale, or another branch | Check the printed ID, sync status, and activated branch |
| Existing return cannot be cancelled | The invoice already has a return | Return any other eligible lines; do not cancel the bill |
| Only _n_ remains returnable | The requested quantity exceeds the remaining units | Reduce the selected quantity |
| Cancelled or already fully returned | The invoice has no valid return state | Review its audit history; do not submit another reversal |
| Original payment allocation is incomplete | Historical payment data cannot cover the refund | Stop and have an administrator reconcile the invoice; do not pay an estimated amount |
| Cannot reach the POS API | Reversals cannot be safely authorized offline | Restore connectivity and use **Settings > Sync now**, then retry |

Never create a second sale, manually increase stock, or apply a negative discount to
imitate a reversal. Those workarounds break payment, shift, tax, and inventory audit
integrity.

## Manager verification checklist

Use a test tenant and branch before production rollout:

1. Grant `sales.cancel`, complete a tracked cash sale, cancel it in the same shift, and
   confirm full stock restoration and a separate cancelled-bill total.
2. Complete a split-payment sale, return one item, and confirm the refund breakdown
   follows the original methods and only the selected stock is restored.
3. Close the original shift, open another, and confirm cancellation is rejected while
   Sales Return remains available.
4. Attempt an excessive quantity, duplicate return, cross-branch lookup, fully returned
   bill, cancelled bill, and Free Guest refund. Each must fail without changing stock.
5. Close the shift and compare POS history/PDF figures with the tenant dashboard.

The POS endpoints used by these screens are `GET /api/v1/pos/sales/by-number/{sale_number}`,
`POST /api/v1/pos/sales/{id}/cancel`, and
`POST /api/v1/pos/sales/{id}/return`. These paths are implementation references for
support and testing; cashiers should use the POS screens.
