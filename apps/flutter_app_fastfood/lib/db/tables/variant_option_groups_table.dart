import 'package:drift/drift.dart';

/// Drift table for shared Variant Option Groups (e.g. "Size") attached to a
/// product — see models/product_variant_option_group.py. Always single-select;
/// there is no min/max_selections here (spec A1), only the per-product
/// [isRequired] override.
class VariantOptionGroupsTable extends Table {
  @override
  String get tableName => 'variant_option_groups';

  TextColumn get id => text()();
  TextColumn get productId => text().named('product_id')();
  TextColumn get name => text()();

  /// When true the cashier must pick one option before adding to cart.
  BoolColumn get isRequired => boolean().named('is_required')();
  IntColumn get displayOrder => integer().named('display_order')();

  /// Laptop Store shareable-inventory model — 'specification' (default,
  /// today's only behavior): options define a combination Variant, unchanged.
  /// 'inventory_component': the POS must offer these options as a dynamic,
  /// independently priced/stocked pick at sale time instead — see
  /// features/pos/widgets/variant_panel.dart's Components section.
  TextColumn get usageType =>
      text().named('usage_type').withDefault(const Constant('specification'))();

  /// JSON-encoded list of allowed VariantOption ids for this product's
  /// attachment (spec §22 — compatibility is product-specific). Empty list
  /// (the default) means every option under this group is offered.
  TextColumn get allowedOptionIds =>
      text().named('allowed_option_ids').withDefault(const Constant('[]'))();

  @override
  Set<Column> get primaryKey => {id};
}
