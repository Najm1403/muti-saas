import 'package:decimal/decimal.dart';
import 'package:uuid/uuid.dart';

import '../../core/models/sale/pos_sale_create.dart';
import '../../core/models/sale/pos_sale_item_create.dart';
import '../../core/models/sale/pos_sale_variant_option_snapshot.dart';
import '../../core/models/sale/pos_sale_addon_selection.dart';
import '../../core/models/sale/pos_sale_payment_create.dart';

/// A selected Variant Option shown on a cart line — display only, no price
/// (spec A1/D4). Pricing for a customization belongs to [CartAddon] instead.
class CartVariantOption {
  final String variantOptionId;
  final String optionName;

  const CartVariantOption({
    required this.variantOptionId,
    required this.optionName,
  });
}

/// A selected (or explicitly removed) Add-on on a cart line.
///
/// [wasRemoved] records that a `default_selected` Add-on Item was unchecked
/// by the cashier — the server still needs to see it removed (spec D7/F2).
class CartAddon {
  final String addonItemId;
  final String addonName;
  final Decimal priceDelta;
  final bool wasRemoved;

  const CartAddon({
    required this.addonItemId,
    required this.addonName,
    required this.priceDelta,
    this.wasRemoved = false,
  });
}

/// A single product line in the active cart.
///
/// Immutable — mutations return a new instance via [copyWith].
/// All monetary arithmetic uses [Decimal] to avoid floating-point drift;
/// values are only converted to String when serializing for the API or DB.
/// [variantId] is required — every cart item resolves to a real synced
/// Variant, never a client-side guess (spec F2/F3).
class CartItem {
  final String id;
  final String variantId;
  final String productId;

  /// Snapshot of the product name at the time it was added to the cart.
  final String productName;

  /// = Variant.sale_price at add-to-cart time.
  final Decimal unitPrice;
  final Decimal quantity;
  final List<CartVariantOption> variantOptions;
  final List<CartAddon> addons;
  final Decimal discount;

  /// Laptop Store shareable-inventory model — set together only when this
  /// line is a selected 'inventory_component' (e.g. a RAM stick) belonging
  /// to another item in this same cart, rather than a standalone product.
  /// This is otherwise an ordinary CartItem — not a nested child — so
  /// pricing/stock code needs no special-casing; only merging is affected
  /// (a component line never merges with another, see [CartService._mergeKey]).
  final String? parentCartItemId;
  final String? satisfiesOptionGroupId;
  final String? componentOptionId;

  CartItem({
    required this.id,
    required this.variantId,
    required this.productId,
    required this.productName,
    required this.unitPrice,
    required this.quantity,
    this.variantOptions = const [],
    this.addons = const [],
    Decimal? discount,
    this.parentCartItemId,
    this.satisfiesOptionGroupId,
    this.componentOptionId,
  }) : discount = discount ?? Decimal.zero;

  /// Sum of every non-removed add-on's price delta.
  Decimal get addonsTotal => addons
      .where((a) => !a.wasRemoved)
      .fold(Decimal.zero, (sum, a) => sum + a.priceDelta);

  /// (unitPrice + addonsTotal) × quantity − item-level discount.
  Decimal get lineTotal => (unitPrice + addonsTotal) * quantity - discount;

  /// Returns a copy with [quantity] and/or [discount] replaced.
  CartItem copyWith({Decimal? quantity, Decimal? discount}) => CartItem(
        id: id,
        variantId: variantId,
        productId: productId,
        productName: productName,
        unitPrice: unitPrice,
        quantity: quantity ?? this.quantity,
        variantOptions: variantOptions,
        addons: addons,
        discount: discount ?? this.discount,
        parentCartItemId: parentCartItemId,
        satisfiesOptionGroupId: satisfiesOptionGroupId,
        componentOptionId: componentOptionId,
      );
}

void _requireWholeQuantity(Decimal quantity) {
  final units = quantity.toBigInt();
  if (units <= BigInt.zero || Decimal.fromBigInt(units) != quantity) {
    throw StateError('Quantities must be positive whole units.');
  }
}

final _canonicalUuid = RegExp(
  r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-8][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$',
);

bool _isUuid(String value) => _canonicalUuid.hasMatch(value);

/// A payment tender being applied to the current cart.
class CartPayment {
  final String paymentMethod;

  /// Amount tendered. Uses [Decimal] for precision; serialized to String on submit.
  final Decimal amount;
  final String? reference;

  const CartPayment({
    required this.paymentMethod,
    required this.amount,
    this.reference,
  });
}

/// An immutable snapshot of the cart at a point in time.
///
/// Produced by [CartService.snapshot] and passed to [SaleRepository.submitSale].
/// Keeping this separate from [CartService] means the mutable service state
/// cannot be altered after a snapshot is taken for submission.
class CartSnapshot {
  final List<CartItem> items;
  final List<CartPayment> payments;
  final Decimal discount;
  final Decimal taxRate;
  final bool taxInclusive;
  final String? promotionId;
  final String? dealId;

  CartSnapshot({
    required this.items,
    required this.payments,
    Decimal? discount,
    Decimal? taxRate,
    this.taxInclusive = false,
    this.promotionId,
    this.dealId,
  })  : discount = discount ?? Decimal.zero,
        taxRate = taxRate ?? Decimal.zero;

  /// Sum of all line totals before the cart-level discount is applied.
  Decimal get subtotal => items.fold(Decimal.zero, (s, i) => s + i.lineTotal);

  /// Tax amount added on top of (subtotal − discount).
  ///
  /// Returns zero when [taxInclusive] is true (tax is baked into prices)
  /// or when [taxRate] is zero (no tax configured).
  Decimal get taxAmount {
    if (taxInclusive || taxRate == Decimal.zero) return Decimal.zero;
    return ((subtotal - discount) * taxRate).round(scale: 2);
  }

  /// Final amount owed: subtotal − cart discount + tax.
  Decimal get total => subtotal - discount + taxAmount;

  /// Converts the snapshot into the API request model for online submission.
  ///
  /// [id] is a client-generated UUID v4; [saleNumber] is the human-readable
  /// identifier built from the sale counter. Both are generated by
  /// [SaleRepository] before this method is called.
  PosSaleCreate toPosSaleCreate({
    required String id,
    required String saleNumber,
    String? sessionId,
  }) {
    for (final item in items) {
      _requireWholeQuantity(item.quantity);
      final componentFields = [
        item.parentCartItemId,
        item.satisfiesOptionGroupId,
        item.componentOptionId,
      ];
      final populated = componentFields.where((value) => value != null).length;
      if (populated != 0 && populated != componentFields.length) {
        throw StateError(
          'The cart contains an incomplete component selection for '
          '"${item.productName}". Remove the configured product and add it again.',
        );
      }
    }
    // Older locally-created component lines used a readable composite key as
    // their ID. Repair such draft/cart IDs at the API boundary while retaining
    // a stable mapping so parent-child references still point to the submitted
    // parent. The backend remains strict and all newly-created lines use UUIDs.
    final submittedItemIds = <String, String>{
      for (final item in items)
        item.id: _isUuid(item.id) ? item.id : const Uuid().v4(),
    };
    for (final item in items) {
      if (item.parentCartItemId != null &&
          !submittedItemIds.containsKey(item.parentCartItemId)) {
        throw StateError(
          'The cart contains an orphaned component "${item.productName}". '
          'Remove the configured product and add it again.',
        );
      }
    }
    final now = DateTime.now().toUtc();
    return PosSaleCreate(
      id: id,
      saleNumber: saleNumber,
      soldAt: now,
      subtotal: subtotal.toString(),
      discount: discount.toString(),
      total: total.toString(),
      taxAmount: taxAmount.toString(),
      // Omit taxRate field entirely when no tax applies.
      taxRate: taxRate == Decimal.zero ? null : taxRate.toString(),
      promotionId: promotionId,
      dealId: dealId,
      sessionId: sessionId,
      items: items
          .map((i) => PosSaleItemCreate(
                // The cart item's own id (not a fresh one per submit) so a
                // component's parentCartItemId reference resolves to the
                // exact id the parent line is actually submitted with.
                id: submittedItemIds[i.id]!,
                variantId: i.variantId,
                productId: i.productId,
                productName: i.productName,
                quantity: i.quantity.toString(),
                unitPrice: i.unitPrice.toString(),
                discount: i.discount.toString(),
                total: i.lineTotal.toString(),
                options: i.variantOptions
                    .map((o) => PosSaleVariantOptionSnapshot(
                          variantOptionId: o.variantOptionId,
                          optionName: o.optionName,
                        ))
                    .toList(),
                addons: i.addons
                    .map((a) => PosSaleAddonSelection(
                          addonItemId: a.addonItemId,
                          addonName: a.addonName,
                          priceDelta: a.priceDelta.toString(),
                          wasRemoved: a.wasRemoved,
                        ))
                    .toList(),
                parentItemId: i.parentCartItemId == null
                    ? null
                    : submittedItemIds[i.parentCartItemId],
                satisfiesOptionGroupId: i.satisfiesOptionGroupId,
                componentOptionId: i.componentOptionId,
              ))
          .toList(),
      payments: payments
          .map((p) => PosSalePaymentCreate(
                paymentMethod: p.paymentMethod,
                amount: p.amount.toString(),
                reference: p.reference,
              ))
          .toList(),
    );
  }
}

/// In-memory source of truth for the sale currently being built by the cashier.
///
/// All state is held in plain Dart lists and primitives — nothing is persisted
/// until [SaleRepository.submitSale] is called with a [snapshot]. The UI reads
/// state by calling [snapshot] or the individual getters; it never mutates the
/// internal lists directly (they are exposed as unmodifiable views).
class CartService {
  final List<CartItem> _items = [];
  final List<CartPayment> _payments = [];
  Decimal _discount = Decimal.zero;
  Decimal _taxRate = Decimal.zero;
  bool _taxInclusive = false;
  String? _promotionId;
  String? _dealId;

  /// Unmodifiable view of current cart items.
  List<CartItem> get items => List.unmodifiable(_items);

  /// Unmodifiable view of current payment tenders.
  List<CartPayment> get payments => List.unmodifiable(_payments);

  Decimal get discount => _discount;

  /// Merge key for [addItem]: same variant + same set of non-removed add-ons
  /// (and their price) collapse into a single line with combined quantity.
  String _mergeKey(CartItem value) {
    // A selected component belongs to one specific parent line — merging
    // two components that happen to share a variant (e.g. two laptops both
    // configured with 16GB RAM) would collapse their 1:1 pairing with their
    // own parent, breaking receipt grouping and the required-group check.
    if (value.parentCartItemId != null) return value.id;
    final addonKey = (value.addons
            .where((a) => !a.wasRemoved)
            .map((a) => '${a.addonItemId}:${a.priceDelta}')
            .toList()
          ..sort())
        .join('|');
    return '${value.variantId}:$addonKey';
  }

  /// Adds [item] to the cart, merging quantity if the same variant + add-on
  /// selection is already present.
  void addItem(CartItem item) {
    _requireWholeQuantity(item.quantity);
    final key = _mergeKey(item);
    final idx = _items.indexWhere((i) =>
        i.unitPrice == item.unitPrice &&
        i.discount == item.discount &&
        _mergeKey(i) == key);
    if (idx >= 0) {
      _items[idx] = _items[idx].copyWith(
        quantity: _items[idx].quantity + item.quantity,
      );
    } else {
      _items.add(item);
    }
  }

  /// Adds one product configuration as an atomic bundle.
  ///
  /// A configured product is represented by a base line plus ordinary child
  /// component lines. Its base must not merge with an existing cart line:
  /// doing so would discard the new base ID while its components continued to
  /// reference it, producing an orphaned component at checkout. Simple items
  /// without components retain the normal quantity-merging behavior.
  void addItems(Iterable<CartItem> additions) {
    final batch = additions.toList(growable: false);
    final componentParentIds = batch
        .map((item) => item.parentCartItemId)
        .whereType<String>()
        .toSet();

    for (final item in batch) {
      if (componentParentIds.contains(item.id)) {
        _requireWholeQuantity(item.quantity);
        _items.add(item);
      } else {
        addItem(item);
      }
    }
  }

  /// Removes the item with [itemId] from the cart, along with any selected
  /// Inventory Components tagged to it via [CartItem.parentCartItemId] —
  /// otherwise an orphaned component would still be submitted at checkout,
  /// referencing a parent line that no longer exists in the sale.
  void removeItem(String itemId) =>
      _items.removeWhere((i) => i.id == itemId || i.parentCartItemId == itemId);

  /// Sets the quantity of [itemId] to [qty]; removes the item (and its
  /// components, see [removeItem]) if [qty] ≤ 0.
  void updateQuantity(String itemId, Decimal qty) {
    final idx = _items.indexWhere((i) => i.id == itemId);
    if (idx >= 0) {
      if (qty <= Decimal.zero) {
        removeItem(itemId);
      } else {
        _requireWholeQuantity(qty);
        _items[idx] = _items[idx].copyWith(quantity: qty);
      }
    }
  }

  /// Sets the cart-level discount amount.
  void setDiscount(Decimal value) => _discount = value;

  /// Sets the tax rate and whether it is inclusive in product prices.
  void setTax({required Decimal rate, required bool inclusive}) {
    _taxRate = rate;
    _taxInclusive = inclusive;
  }

  /// Associates a promotion with this cart (or clears it when [id] is null).
  void setPromotion(String? id) => _promotionId = id;

  /// Associates a deal with this cart (or clears it when [id] is null).
  void setDeal(String? id) => _dealId = id;

  /// Appends a payment tender to the cart.
  void addPayment(CartPayment payment) => _payments.add(payment);

  /// Removes all payment tenders (e.g. when the cashier changes the payment method).
  void clearPayments() => _payments.clear();

  /// Returns an immutable snapshot of the current cart state for submission.
  CartSnapshot snapshot() => CartSnapshot(
        items: List.from(_items),
        payments: List.from(_payments),
        discount: _discount,
        taxRate: _taxRate,
        taxInclusive: _taxInclusive,
        promotionId: _promotionId,
        dealId: _dealId,
      );

  /// Resets the cart to empty after a sale is completed.
  ///
  /// Tax rate is intentionally preserved across sales so the cashier does not
  /// have to re-select it for every transaction.
  void clear() {
    _items.clear();
    _payments.clear();
    _discount = Decimal.zero;
    _promotionId = null;
    _dealId = null;
  }
}
