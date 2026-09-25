import 'package:drift/drift.dart';

/// Drift table for individual Variant Options (e.g. "Large") within a
/// [VariantOptionsTable] group's parent group. No price here — a Variant
/// Option only ever defines the SKU; a price delta is an Add-on's job
/// (spec A1/D4 — never conflate the two).
class VariantOptionsTable extends Table {
  @override
  String get tableName => 'variant_options';

  TextColumn get id => text()();
  TextColumn get optionGroupId => text().named('option_group_id')();
  TextColumn get name => text()();
  IntColumn get displayOrder => integer().named('display_order')();
  BoolColumn get isActive => boolean().named('is_active')();

  /// Laptop Store shareable-inventory model — set only when this option is
  /// tracked as a shared inventory component. Resolves this option's own
  /// price/stock via [VariantsTable] (the component's own real Variant) —
  /// no separate data source needed.
  TextColumn get componentVariantId =>
      text().named('component_variant_id').nullable()();

  @override
  Set<Column> get primaryKey => {id};
}
