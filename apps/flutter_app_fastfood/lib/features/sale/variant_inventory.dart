import 'package:decimal/decimal.dart';

import '../../db/app_database.dart';
import 'cart_service.dart';

/// Real, DAO-backed stock checks against the synced `variants` /
/// `variant_branch_stock` tables (spec F5) — no more
/// JSON-blob-in-settings shim. Every check resolves a real [VariantsTableData]
/// row; the POS never synthesizes stock for a variant that hasn't synced.
class VariantInventory {
  final AppDatabase db;
  VariantInventory(this.db);

  int _inCart(CartSnapshot cart, String variantId) => cart.items
      .where((i) => i.variantId == variantId)
      .fold<int>(0, (sum, i) => sum + i.quantity.toBigInt().toInt());

  /// Returns the reason [variantId] cannot be sold at [quantity] right now,
  /// or null when the sale is ready to add.
  Future<String?> selectionError(
      String variantId, int quantity, CartSnapshot cart) async {
    final variant = await db.menuDao.variantById(variantId);
    if (variant == null) return 'Sync to see variant availability';
    if (!variant.sellable) {
      return variant.sellableReason ??
          'This combination is unavailable. Sync the menu or create its variant in Inventory.';
    }
    if (!variant.allowInventoryTracking || !variant.tracksInventory) {
      return null;
    }
    final stock = await db.menuDao.branchStockForVariant(variantId);
    final available = stock?.quantity ?? 0;
    final requested = _inCart(cart, variantId) + quantity;
    if (requested > available) {
      return 'Insufficient variant stock: $available available, $requested requested';
    }
    return null;
  }

  /// Aggregates cart quantities per variant, rejecting fractional units.
  Map<String, int> demandByVariant(CartSnapshot cart) {
    final demand = <String, int>{};
    for (final item in cart.items) {
      final units = item.quantity.toBigInt().toInt();
      if (units <= 0 || Decimal.fromInt(units) != item.quantity) {
        throw StateError('Quantities must be positive whole units.');
      }
      demand[item.variantId] = (demand[item.variantId] ?? 0) + units;
    }
    return demand;
  }

  /// Validates [demand] against synced stock, throwing when any tracked
  /// variant is oversold.
  Future<void> validateDemand(Map<String, int> demand) async {
    for (final entry in demand.entries) {
      final variant = await db.menuDao.variantById(entry.key);
      if (variant == null) {
        throw StateError('Variant inventory is incomplete. Sync the menu.');
      }
      if (!variant.allowInventoryTracking || !variant.tracksInventory) {
        continue;
      }
      final stock = await db.menuDao.branchStockForVariant(entry.key);
      final available = stock?.quantity;
      if (available == null || entry.value > available) {
        throw StateError(
            'Insufficient variant stock: ${available ?? 0} available, ${entry.value} requested.');
      }
    }
  }

  Future<void> _consumeQuantityStock(Map<String, int> demand) async {
    for (final entry in demand.entries) {
      final variant = await db.menuDao.variantById(entry.key);
      if (variant == null) continue;
      if (!variant.allowInventoryTracking || !variant.tracksInventory) {
        continue;
      }
      final stock = await db.menuDao.branchStockForVariant(entry.key);
      if (stock == null) continue;
      final after = stock.quantity - entry.value;
      await db.menuDao.setBranchStock(
          stock.variantId, stock.branchId, after < 0 ? 0 : after);
    }
  }

  /// Server-approved sales consume the cached quantity too, without rejecting
  /// a completed payment based on a stale local snapshot.
  Future<void> consumeConfirmed(CartSnapshot cart) async {
    await db.transaction(() async {
      Map<String, int> demand;
      try {
        demand = demandByVariant(cart);
      } on StateError {
        // Payment already succeeded — don't fail the flow retroactively.
        return;
      }
      await _consumeQuantityStock(demand);
    });
  }

  /// Called in the same database transaction that queues the offline sale.
  Future<void> reserve(CartSnapshot cart) async {
    final demand = demandByVariant(cart);
    await validateDemand(demand);
    await _consumeQuantityStock(demand);
  }
}
