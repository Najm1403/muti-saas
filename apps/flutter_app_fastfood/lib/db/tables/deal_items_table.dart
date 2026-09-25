import 'package:drift/drift.dart';

/// Drift table definition for the individual product/category slots within a deal.
///
/// Each row belongs to one [DealsTable] row. Either [productId] or [categoryId]
/// is set — when [categoryId] is used, any product from that category satisfies
/// the slot. [isFree] marks slots whose items are included at no charge.
class DealItemsTable extends Table {
  @override
  String get tableName => 'deal_items';

  TextColumn get id => text()();
  TextColumn get dealId => text().named('deal_id')();

  /// Specific product for this slot; null when any product in [categoryId] qualifies.
  TextColumn get productId => text().nullable().named('product_id')();

  /// Category constraint; null when a specific [productId] is required.
  TextColumn get categoryId => text().nullable().named('category_id')();
  IntColumn get quantity => integer()();
  BoolColumn get isFree => boolean().named('is_free')();
  IntColumn get sortOrder => integer().named('sort_order')();

  @override
  Set<Column> get primaryKey => {id};
}
