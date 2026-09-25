import 'package:drift/drift.dart';

/// Drift table definition for tax rate configurations synced from the cloud.
///
/// [rate] is stored as TEXT (e.g. "0.15" for 15%) to avoid float precision issues.
/// At most one row should have [isDefault] = true; that rate is applied automatically
/// at checkout via [TaxDao.defaultRate].
class TaxRatesTable extends Table {
  @override
  String get tableName => 'tax_rates';

  TextColumn get id => text()();
  TextColumn get name => text()();

  /// Decimal rate value stored as TEXT, e.g. "0.10" for 10%.
  TextColumn get rate => text()();

  /// True when the tax is already included in product prices (no extra charge at checkout).
  BoolColumn get isInclusive => boolean().named('is_inclusive')();
  BoolColumn get isDefault => boolean().named('is_default')();

  @override
  Set<Column> get primaryKey => {id};
}
