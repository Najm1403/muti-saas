import 'package:drift/drift.dart';

/// Drift table for selected Add-ons on an offline-queued sale item.
///
/// Mirrors [LocalSaleItemOptionsTable] but for priced Add-ons (spec D7).
/// [wasRemoved] records that a `default_selected` Add-on Item was
/// unchecked by the cashier — the server still needs to see it removed.
class LocalSaleItemAddonsTable extends Table {
  @override
  String get tableName => 'local_sale_item_addons';

  TextColumn get id => text()();
  TextColumn get saleItemId => text().named('sale_item_id')();
  TextColumn get addonItemId => text().named('addon_item_id')();

  /// Snapshot of the add-on name at sale time.
  TextColumn get addonName => text().named('addon_name')();

  /// Price delta as TEXT (Decimal), client-submitted; server re-verifies.
  TextColumn get priceDelta => text().named('price_delta')();
  BoolColumn get wasRemoved => boolean()
      .named('was_removed')
      .withDefault(const Constant(false))();

  @override
  Set<Column> get primaryKey => {id};
}
