import 'package:drift/drift.dart';

/// Drift table for payment tenders attached to an offline-queued sale.
///
/// A single sale may have multiple rows here (split payments across methods).
/// Each row is a child of [LocalSalesTable] via [saleId].
/// [amount] is stored as TEXT to preserve Decimal precision.
class LocalPaymentsTable extends Table {
  @override
  String get tableName => 'local_payments';

  TextColumn get id => text()();
  TextColumn get saleId => text().named('sale_id')();
  TextColumn get paymentMethod => text().named('payment_method')();

  /// Amount tendered for this payment method. Stored as TEXT (Decimal).
  TextColumn get amount => text()();

  /// Optional transaction or card authorization reference.
  TextColumn get reference => text().nullable()();

  @override
  Set<Column> get primaryKey => {id};
}
