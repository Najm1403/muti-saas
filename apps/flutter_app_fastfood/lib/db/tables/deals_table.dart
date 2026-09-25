import 'package:drift/drift.dart';

/// Drift table definition for bundled deals synced from the cloud.
///
/// A deal groups multiple products at a fixed price or a discount. The actual
/// line items (what products/categories are included) are stored in [DealItemsTable].
/// Monetary fields use TEXT to preserve Decimal precision.
class DealsTable extends Table {
  @override
  String get tableName => 'deals';

  TextColumn get id => text()();
  TextColumn get name => text()();
  TextColumn get description => text().nullable()();
  TextColumn get dealCode => text().named('deal_code')();

  /// Fixed bundle price as TEXT (Decimal); null when discount-based pricing is used.
  TextColumn get fixedPrice => text().nullable().named('fixed_price')();

  /// Discount magnitude as TEXT (Decimal); interpreted alongside [discountType].
  TextColumn get discountValue => text().nullable().named('discount_value')();

  /// "flat" or "percent" — how [discountValue] is applied.
  TextColumn get discountType => text().nullable().named('discount_type')();
  DateTimeColumn get validFrom => dateTime().nullable().named('valid_from')();
  DateTimeColumn get validUntil => dateTime().nullable().named('valid_until')();
  BoolColumn get isActive => boolean().named('is_active')();

  @override
  Set<Column> get primaryKey => {id};
}
