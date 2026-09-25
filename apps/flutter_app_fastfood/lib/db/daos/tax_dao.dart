import 'package:drift/drift.dart';
import '../app_database.dart';
import '../tables/tax_rates_table.dart';

part 'tax_dao.g.dart';

/// DAO for tax rate read and write operations.
///
/// Kept separate from [MenuDao] because tax rates are consumed by sale
/// calculation logic independently of the menu catalog.
@DriftAccessor(tables: [TaxRatesTable])
class TaxDao extends DatabaseAccessor<AppDatabase> with _$TaxDaoMixin {
  TaxDao(super.db);

  /// Returns all tax rates configured for this branch.
  Future<List<TaxRatesTableData>> allRates() => select(taxRatesTable).get();

  /// Returns the single tax rate marked as default, or null if none is set.
  ///
  /// Used by [CartService] to auto-apply tax at checkout without cashier input.
  Future<TaxRatesTableData?> defaultRate() =>
      (select(taxRatesTable)..where((t) => t.isDefault.equals(true)))
          .getSingleOrNull();

  /// Upserts [rows] into the tax_rates table; existing rows are fully replaced.
  Future<void> upsertRates(List<TaxRatesTableCompanion> rows) =>
      batch((b) => b.insertAllOnConflictUpdate(taxRatesTable, rows));
}
