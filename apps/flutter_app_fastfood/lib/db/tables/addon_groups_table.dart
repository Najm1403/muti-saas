import 'package:drift/drift.dart';

/// Drift table for shared Add-on Groups (e.g. "Toppings") attached to a
/// product — see models/product_addon_group.py. Structurally separate from
/// Variant Option Groups; never feeds into variant generation (spec A1/D4).
class AddonGroupsTable extends Table {
  @override
  String get tableName => 'addon_groups';

  TextColumn get id => text()();
  TextColumn get productId => text().named('product_id')();
  TextColumn get name => text()();
  TextColumn get selectionType => text().named('selection_type')();
  IntColumn get minSelect => integer().named('min_select')();
  IntColumn get maxSelect => integer().nullable().named('max_select')();
  IntColumn get displayOrder => integer().named('display_order')();

  @override
  Set<Column> get primaryKey => {id};
}
