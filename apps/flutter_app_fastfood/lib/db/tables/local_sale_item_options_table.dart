import 'package:drift/drift.dart';

/// Drift table for selected Variant Options on an offline sale item.
///
/// Each row is a child of [LocalSaleItemsTable] via [saleItemId]. Display/audit
/// snapshot only — Variant Options carry no price (spec A1/D4; pricing lives
/// on [LocalSaleItemAddonsTable] instead). The physical column stays named
/// `product_option_id` for migration continuity even though it now holds a
/// VariantOption id.
class LocalSaleItemOptionsTable extends Table {
  @override
  String get tableName => 'local_sale_item_options';

  TextColumn get id => text()();
  TextColumn get saleItemId => text().named('sale_item_id')();
  TextColumn get variantOptionId => text().named('product_option_id')();

  /// Snapshot of option name at sale time.
  TextColumn get optionName => text().named('option_name')();

  /// Retired — Variant Options no longer carry a price (spec A1/D4). Kept
  /// physically for migration continuity; always written as "0.00".
  TextColumn get priceAdjustment => text().named('price_adjustment')();

  @override
  Set<Column> get primaryKey => {id};
}
