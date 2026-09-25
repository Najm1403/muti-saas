import 'package:drift/drift.dart';

/// Drift table for individual Add-on Items (e.g. "Extra Cheese") within an
/// Add-on Group. [priceDelta] is real pricing, always re-verified server-side
/// against this same value at sale time (spec D7) — never trusted blindly.
class AddonItemsTable extends Table {
  @override
  String get tableName => 'addon_items';

  TextColumn get id => text()();
  TextColumn get addonGroupId => text().named('addon_group_id')();
  TextColumn get name => text()();
  TextColumn get priceDelta => text().named('price_delta')();
  BoolColumn get defaultSelected => boolean()
      .named('default_selected')
      .withDefault(const Constant(false))();
  IntColumn get displayOrder => integer().named('display_order')();
  BoolColumn get isActive => boolean().named('is_active')();

  @override
  Set<Column> get primaryKey => {id};
}
