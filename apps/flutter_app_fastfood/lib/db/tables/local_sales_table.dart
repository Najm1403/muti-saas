import 'package:drift/drift.dart';

/// Drift table for retained device sale history and the offline outbox.
///
/// Online-confirmed and offline-created sales are retained for reporting.
/// Unsynced rows are uploaded in batch and are never removed by retention.
/// All monetary fields use TEXT to preserve Decimal precision.
class LocalSalesTable extends Table {
  @override
  String get tableName => 'local_sales';

  /// Client-generated UUID v4 — preserved as the server-side primary key on upload.
  TextColumn get id => text()();

  /// Human-readable sale number unique per device (e.g. "S2024000001").
  /// UNIQUE constraint lets [SaleDao.saleByNumber] quickly detect duplicates.
  TextColumn get originProof => text().nullable().named('origin_proof')();
  TextColumn get sessionId => text().nullable().named('session_id')();
  TextColumn get cashierId => text().nullable().named('cashier_id')();

  TextColumn get saleNumber => text().named('sale_number').unique()();
  DateTimeColumn get soldAt => dateTime().named('sold_at')();

  /// The signed-in cashier's display name at the moment of submission.
  /// Captured client-side because an offline-queued sale has no server
  /// round-trip to resolve it from `user_id` until it syncs.
  TextColumn get cashierName => text().nullable().named('cashier_name')();

  /// Authoritative cloud status when known. Queued rows remain COMPLETED
  /// locally because they represent finalized, not draft, transactions.
  TextColumn get status => text().withDefault(const Constant('COMPLETED'))();

  /// Pre-discount, pre-tax item total. Stored as TEXT (Decimal).
  TextColumn get subtotal => text()();
  TextColumn get discount => text()();
  TextColumn get total => text()();
  TextColumn get taxAmount => text().named('tax_amount')();
  TextColumn get taxRate => text().nullable().named('tax_rate')();
  TextColumn get promotionId => text().nullable().named('promotion_id')();
  TextColumn get dealId => text().nullable().named('deal_id')();

  /// False until this sale has been successfully uploaded to the server.
  BoolColumn get synced => boolean().withDefault(const Constant(false))();
  DateTimeColumn get createdAt =>
      dateTime().named('created_at').withDefault(currentDateAndTime)();

  /// True once the server has rejected this sale for a deterministic reason
  /// (see [PosUploadResult.retryable]) — retrying would fail identically, so
  /// [SaleDao.unsynced] excludes it from future upload batches instead of
  /// resubmitting it on every sync tick forever. Surfaced to the cashier via
  /// [syncError] until an admin resolves it server-side.
  BoolColumn get needsReview =>
      boolean().named('needs_review').withDefault(const Constant(false))();

  /// The server's rejection message, retained for [needsReview] sales so the
  /// sync status banner can keep showing it after the sale stops retrying.
  TextColumn get syncError => text().nullable().named('sync_error')();

  @override
  Set<Column> get primaryKey => {id};
}
