import 'package:flutter_test/flutter_test.dart';
import 'package:decimal/decimal.dart';
import 'package:fastfood_pos/features/pos/pos_state.dart';
import 'package:fastfood_pos/features/sale/cart_service.dart';

void main() {
  test('parked drafts are RAM-only: a fresh notifier never sees them', () {
    // Parking a ticket must never touch disk — a new DraftNotifier instance
    // (what happens on every app launch, and on every cashier switch, since
    // draftNotifierProvider watches authNotifierProvider) starts empty
    // regardless of what an earlier instance parked.
    final original = DraftNotifier();
    original.park(ticketLabel: 'Saved order', items: [
      CartItem(
          id: 'line',
          variantId: 'variant-1',
          productId: 'product',
          productName: 'Meal',
          unitPrice: Decimal.parse('9.99'),
          quantity: Decimal.one,
          addons: [
            CartAddon(
                addonItemId: 'addon-1',
                addonName: 'Extra',
                priceDelta: Decimal.parse('1.50'))
          ])
    ], taxRate: Decimal.parse('0.17'), taxInclusive: false);
    expect(original.state.single.items.single.lineTotal, Decimal.parse('11.49'));
    original.dispose();

    final freshInstance = DraftNotifier();
    expect(freshInstance.state, isEmpty);
    freshInstance.dispose();
  });

  test('removing a draft updates state synchronously', () {
    final notifier = DraftNotifier();
    notifier.park(
        ticketLabel: 'Ticket #1',
        items: [
          CartItem(
              id: 'line',
              variantId: 'variant-1',
              productId: 'product',
              productName: 'Meal',
              unitPrice: Decimal.parse('9.99'),
              quantity: Decimal.one)
        ],
        taxRate: Decimal.zero,
        taxInclusive: false);
    final draftId = notifier.state.single.id;
    notifier.remove(draftId);
    expect(notifier.state, isEmpty);
    notifier.dispose();
  });

  test('different customizations remain separate cart lines', () {
    final cart = CartService();
    cart.addItem(CartItem(
        id: 'plain',
        variantId: 'v1',
        productId: 'meal',
        productName: 'Meal',
        unitPrice: Decimal.fromInt(10),
        quantity: Decimal.one));
    cart.addItem(CartItem(
        id: 'extra',
        variantId: 'v1',
        productId: 'meal',
        productName: 'Meal',
        unitPrice: Decimal.fromInt(10),
        quantity: Decimal.one,
        addons: [
          CartAddon(
              addonItemId: 'extra',
              addonName: 'Extra',
              priceDelta: Decimal.fromInt(2))
        ]));
    expect(cart.items.length, 2);
    expect(cart.snapshot().total, Decimal.fromInt(22));
  });
}
