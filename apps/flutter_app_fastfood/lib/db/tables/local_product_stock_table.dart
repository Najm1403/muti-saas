import 'package:drift/drift.dart';

/// Current stock quantity for one tracked product, as last synced from the
/// cloud (the device only ever holds one branch's data — see
/// SettingsDao.getBranchId — so no branch_id column is needed here, unlike
/// the backend's ProductStock which is keyed per branch).
///
/// The tablet only ever displays this number, decrementing it locally as an
/// optimistic hint the moment a sale is queued/submitted so the order-picker
/// doesn't oversell between syncs; the next full/delta sync always
/// overwrites it with the cloud's authoritative value.
class LocalProductStockTable extends Table {
  @override
  String get tableName => 'local_product_stock';

  TextColumn get productId => text().named('product_id')();

  /// Stored as TEXT to avoid floating-point precision loss, matching
  /// ProductsTable.basePrice's convention.
  TextColumn get quantity => text()();

  @override
  Set<Column> get primaryKey => {productId};
}
