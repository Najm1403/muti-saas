import 'package:drift/drift.dart';

/// Drift table definition for discount promotions synced from the cloud.
///
/// Promotions are applied automatically (trigger-based) or manually via
/// [promoCode]. Trigger columns are mutually exclusive — only one is set
/// per row depending on how the promotion was configured in the back-office.
/// Monetary fields use TEXT to preserve Decimal precision.
class PromotionsTable extends Table {
  @override
  String get tableName => 'promotions';

  TextColumn get id => text()();
  TextColumn get name => text()();

  /// Cashier-entered code to activate this promotion; null for automatic promotions.
  TextColumn get promoCode => text().nullable().named('promo_code')();

  /// Discount type string, e.g. "percent", "flat", "bogo".
  TextColumn get type => text()();

  /// Discount magnitude as TEXT (Decimal); meaning depends on [type].
  TextColumn get discountValue => text().named('discount_value')();
  IntColumn get triggerMinQty => integer().nullable().named('trigger_min_qty')();
  TextColumn get triggerMinAmount => text().nullable().named('trigger_min_amount')();
  TextColumn get triggerProductId => text().nullable().named('trigger_product_id')();
  TextColumn get triggerCategoryId => text().nullable().named('trigger_category_id')();
  DateTimeColumn get validFrom => dateTime().nullable().named('valid_from')();
  DateTimeColumn get validUntil => dateTime().nullable().named('valid_until')();

  /// Null means unlimited uses; enforced server-side on upload.
  IntColumn get maxUses => integer().nullable().named('max_uses')();

  /// Synced from server for display only — the server is authoritative for enforcement.
  IntColumn get usedCount => integer().named('used_count').withDefault(const Constant(0))();
  BoolColumn get isActive => boolean().named('is_active')();

  @override
  Set<Column> get primaryKey => {id};
}
