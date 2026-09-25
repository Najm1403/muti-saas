import 'package:drift/drift.dart';

/// Drift table definition for menu products synced from the cloud.
///
/// [basePrice] is stored as TEXT (String) rather than REAL to preserve
/// Decimal precision across the DB → JSON → server round-trip.
/// Rows are never created locally — only upserted during sync.
class ProductsTable extends Table {
  @override
  String get tableName => 'products';

  TextColumn get id => text()();
  TextColumn get categoryId => text().named('category_id')();
  TextColumn get productCode => text().named('product_code')();
  TextColumn get name => text()();
  TextColumn get description => text().nullable()();

  /// Stored as TEXT to avoid floating-point precision loss.
  TextColumn get basePrice => text().named('base_price')();
  TextColumn get imagePath => text().nullable().named('image_path')();
  IntColumn get displayOrder => integer().named('display_order')();
  BoolColumn get isActive => boolean().named('is_active')();

  /// Product-level inventory flags — see LocalProductStockTable for the
  /// actual branch-scoped quantity.
  BoolColumn get trackInventory =>
      boolean().named('track_inventory').withDefault(const Constant(false))();
  BoolColumn get allowNegativeStock => boolean()
      .named('allow_negative_stock')
      .withDefault(const Constant(false))();

  @override
  Set<Column> get primaryKey => {id};
}
