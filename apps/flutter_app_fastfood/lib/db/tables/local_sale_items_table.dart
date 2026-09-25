import 'package:drift/drift.dart';

/// Drift table for the line items belonging to an offline-queued sale.
///
/// Each row is a child of [LocalSalesTable] via [saleId]. [productName] is
/// snapshotted at sale time so receipts remain accurate if the catalog changes.
/// All monetary fields use TEXT to preserve Decimal precision.
class LocalSaleItemsTable extends Table {
  @override
  String get tableName => 'local_sale_items';

  TextColumn get id => text()();
  TextColumn get saleId => text().named('sale_id')();
  TextColumn get variantId => text().named('variant_id').nullable()();
  TextColumn get productId => text().named('product_id')();

  /// Name captured at sale time — not a foreign key so it survives catalog renames.
  TextColumn get productName => text().named('product_name')();
  TextColumn get quantity => text()();
  TextColumn get unitPrice => text().named('unit_price')();
  TextColumn get discount => text()();
  TextColumn get total => text()();

  /// Laptop Store shareable-inventory model — set together only on a
  /// selected 'inventory_component' line (e.g. a RAM stick), which is
  /// otherwise an ordinary row in this same table, not a nested child —
  /// see cart_service.dart's CartItem. Null for every normal item.
  TextColumn get parentItemId => text().named('parent_item_id').nullable()();
  TextColumn get satisfiesOptionGroupId =>
      text().named('satisfies_option_group_id').nullable()();
  TextColumn get componentOptionId =>
      text().named('component_option_id').nullable()();

  @override
  Set<Column> get primaryKey => {id};
}
