import 'package:decimal/decimal.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../features/sale/cart_service.dart';
import 'repository_providers.dart';
import 'menu_provider.dart';

part 'cart_notifier.g.dart';

/// Reactive facade over [CartService] that exposes the cart as a [CartSnapshot].
///
/// The underlying [CartService] holds mutable state; this notifier converts
/// every mutation into a new [CartSnapshot] so widgets rebuild reactively.
/// keepAlive ensures the cart survives tab or widget-tree rebuilds.
@Riverpod(keepAlive: true)
class CartNotifier extends _$CartNotifier {
  CartService get _cart => ref.read(cartServiceProvider);

  @override
  CartSnapshot build() {
    final cart = ref.watch(cartServiceProvider);
    final tax = ref.watch(defaultTaxRateProvider).valueOrNull;
    cart.setTax(rate: tax == null ? Decimal.zero : Decimal.parse(tax.rate) * Decimal.parse('0.01'),
      inclusive: tax?.isInclusive ?? false);
    return cart.snapshot();
  }

  void _refresh() => state = _cart.snapshot();

  /// Adds [item] to the cart, incrementing quantity if already present.
  void addItem(CartItem item) {
    _cart.addItem(item);
    _refresh();
  }

  /// Adds a base product and its selected component lines as one bundle.
  void addItems(Iterable<CartItem> items) {
    _cart.addItems(items);
    _refresh();
  }

  /// Removes the item identified by [itemId] from the cart.
  void removeItem(String itemId) {
    _cart.removeItem(itemId);
    _refresh();
  }

  /// Updates the quantity of [itemId]; removes the item when [qty] ≤ 0.
  void updateQuantity(String itemId, Decimal qty) {
    _cart.updateQuantity(itemId, qty);
    _refresh();
  }

  /// Sets the cart-level discount amount.
  void setDiscount(Decimal value) {
    _cart.setDiscount(value);
    _refresh();
  }

  /// Sets the tax rate and whether it is already included in product prices.
  void setTax({required Decimal rate, required bool inclusive}) {
    _cart.setTax(rate: rate, inclusive: inclusive);
    _refresh();
  }

  /// Associates a promotion (or clears with null) with the current cart.
  void setPromotion(String? id) {
    _cart.setPromotion(id);
    _refresh();
  }

  /// Associates a deal (or clears with null) with the current cart.
  void setDeal(String? id) {
    _cart.setDeal(id);
    _refresh();
  }

  /// Appends a payment tender to the current cart.
  void addPayment(CartPayment payment) {
    _cart.addPayment(payment);
    _refresh();
  }

  /// Removes all payment tenders (e.g. when the cashier changes payment method).
  void clearPayments() {
    _cart.clearPayments();
    _refresh();
  }

  /// Resets items, payments, and discount while preserving the tax rate.
  void clear() {
    _cart.clear();
    _refresh();
  }
}
