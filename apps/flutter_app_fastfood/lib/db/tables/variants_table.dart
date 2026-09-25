import 'package:drift/drift.dart';

/// Drift table for composed Variants — the real, sellable SKUs (spec D1/D2).
///
/// Every product always has at least a zero-option default Variant.
/// [optionValueIds] is a JSON-encoded sorted list of VariantOption ids
/// (empty array for the default variant). Never populated from AddonItem ids.
class VariantsTable extends Table {
  @override
  String get tableName => 'variants';

  TextColumn get id => text()();
  TextColumn get productId => text().named('product_id')();

  /// JSON-encoded list of VariantOption ids composing this SKU.
  TextColumn get optionValueIds => text().named('option_value_ids')();

  TextColumn get salePrice => text().named('sale_price')();
  TextColumn get costPrice => text().nullable().named('cost_price')();
  TextColumn get comparePrice => text().nullable().named('compare_price')();
  BoolColumn get tracksInventory =>
      boolean().named('tracks_inventory').withDefault(const Constant(false))();
  BoolColumn get isDefault =>
      boolean().named('is_default').withDefault(const Constant(false))();

  /// Server-computed sellability (e.g. false when required groups can't be
  /// satisfied). The POS must never synthesize a variant client-side — only
  /// ever match against rows synced here.
  BoolColumn get sellable => boolean().withDefault(const Constant(true))();

  /// Human-readable reason when [sellable] is false (e.g. "missing a
  /// selection for a required Variant Option Group"), so the cashier sees
  /// the real cause instead of a generic message. Null when sellable.
  TextColumn get sellableReason => text().nullable().named('sellable_reason')();

  /// Product-level master inventory switch, denormalized here for convenience
  /// so stock checks don't need a join back to [ProductsTable].
  BoolColumn get allowInventoryTracking => boolean()
      .named('allow_inventory_tracking')
      .withDefault(const Constant(false))();
  TextColumn get productName => text().nullable().named('product_name')();
  TextColumn get variantName => text().nullable().named('variant_name')();

  @override
  Set<Column> get primaryKey => {id};
}
