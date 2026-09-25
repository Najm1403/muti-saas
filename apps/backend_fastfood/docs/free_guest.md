# Free Guest checkout

In Tenant Dashboard > Users, create or edit a cashier and enable **Allow Free Guest in POS**.
It defaults to off. Changing this permission requires the existing `users.manage`
permission or the tenant administrative permission recognized by the backend.

The cashier sees **Free Guest** alongside Cash, JazzCash and the other payment
options on the Take Payment screen. It makes the current whole order complimentary:
item prices remain visible, an order discount covers the subtotal, the total and
payment are zero, and inventory is deducted normally. Receipts and payment-method
reports retain the Free Guest label without counting any money as collected.
Positive cash refunds for these orders are rejected.

Free Guest requires connectivity. Checkout refreshes the current cashier permission
when opened and every 15 seconds while visible; the server checks the current
permission again on submission. Denied, deactivated and cross-tenant users cannot
use it. These sales are never silently queued offline on a connection failure.

Apply migration `f9a10b2c3d45` with `python -m alembic upgrade head` before starting
the updated backend. Rebuild/restart the POS app for the new checkout UI. Existing
users remain denied until explicitly granted. No existing cashier was granted
permission by this migration.
