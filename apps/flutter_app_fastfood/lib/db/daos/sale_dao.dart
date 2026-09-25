import 'package:drift/drift.dart';
import '../app_database.dart';
import '../tables/local_sales_table.dart';
import '../tables/local_sale_items_table.dart';
import '../tables/local_sale_item_options_table.dart';
import '../tables/local_sale_item_addons_table.dart';
import '../tables/local_payments_table.dart';

part 'sale_dao.g.dart';

/// DAO for retained sale history and offline outbox operations.
///
/// Handles atomic sale snapshots, local report queries, the unsynced outbox,
/// cloud status updates, and safe retention cleanup.
@DriftAccessor(tables: [
  LocalSalesTable,
  LocalSaleItemsTable,
  LocalSaleItemOptionsTable,
  LocalSaleItemAddonsTable,
  LocalPaymentsTable,
])
class SaleDao extends DatabaseAccessor<AppDatabase> with _$SaleDaoMixin {
  SaleDao(super.db);

  /// Looks up a local sale by its human-readable [saleNumber].
  ///
  /// Used to detect whether a sale has already been queued before marking
  /// it synced after an online submission.
  Future<LocalSalesTableData?> saleByNumber(String saleNumber) =>
      (select(localSalesTable)..where((t) => t.saleNumber.equals(saleNumber)))
          .getSingleOrNull();

  /// Returns all sales that have not yet been uploaded to the server and are
  /// still eligible to be retried — excludes [needsReviewSales], which the
  /// server has already permanently rejected (see [markNeedsReview]).
  Future<List<LocalSalesTableData>> unsynced() => (select(localSalesTable)
        ..where((t) => t.synced.equals(false) & t.needsReview.equals(false)))
      .get();

  /// Sales the server rejected for a deterministic reason (see
  /// [PosUploadResult.retryable]) — excluded from [unsynced] so they stop
  /// being resubmitted, but still unsynced from the server's point of view
  /// until an admin resolves the underlying data issue.
  Future<List<LocalSalesTableData>> needsReviewSales() =>
      (select(localSalesTable)..where((t) => t.needsReview.equals(true)))
          .get();

  /// Sales retained on this device, newest first (including uploaded sales).
  Future<List<LocalSalesTableData>> recentSales({
    DateTime? dateFrom,
    DateTime? dateTo,
    String? sessionId,
    String? cashierId,
  }) {
    final query = select(localSalesTable);
    if (dateFrom != null) {
      query.where((t) => t.soldAt.isBiggerOrEqualValue(dateFrom));
    }
    if (dateTo != null) {
      query.where((t) => t.soldAt.isSmallerOrEqualValue(dateTo));
    }
    if (sessionId != null) {
      query.where((t) => t.sessionId.equals(sessionId));
    }
    if (cashierId != null) {
      query.where((t) => t.cashierId.equals(cashierId));
    }
    query.orderBy([(t) => OrderingTerm.desc(t.soldAt)]);
    return query.get();
  }

  /// Updates the cached status after an authoritative cloud action.
  Future<void> updateStatus(String saleId, String status) async {
    await (update(localSalesTable)..where((t) => t.id.equals(saleId)))
        .write(LocalSalesTableCompanion(status: Value(status)));
  }

  /// Deletes only old, synced history. Unsynced outbox rows are never purged.
  Future<int> pruneSyncedOlderThan(DateTime cutoff) async {
    final oldSales = await (select(localSalesTable)
          ..where((t) =>
              t.synced.equals(true) & t.soldAt.isSmallerThanValue(cutoff)))
        .get();
    final saleIds = oldSales.map((sale) => sale.id).toList();
    if (saleIds.isEmpty) return 0;

    final itemRows = await (select(localSaleItemsTable)
          ..where((t) => t.saleId.isIn(saleIds)))
        .get();
    final itemIds = itemRows.map((item) => item.id).toList();

    await transaction(() async {
      if (itemIds.isNotEmpty) {
        await (delete(localSaleItemOptionsTable)
              ..where((t) => t.saleItemId.isIn(itemIds)))
            .go();
        await (delete(localSaleItemAddonsTable)
              ..where((t) => t.saleItemId.isIn(itemIds)))
            .go();
      }
      await (delete(localSaleItemsTable)..where((t) => t.saleId.isIn(saleIds)))
          .go();
      await (delete(localPaymentsTable)..where((t) => t.saleId.isIn(saleIds)))
          .go();
      await (delete(localSalesTable)..where((t) => t.id.isIn(saleIds))).go();
    });
    return saleIds.length;
  }

  /// Inserts a complete sale with all its items, options, add-ons, and
  /// payments atomically.
  ///
  /// The entire operation runs inside a [transaction] so a partial failure
  /// (e.g. an item insert crashing) leaves no orphaned sale header rows.
  Future<void> insertSaleWithItems({
    required LocalSalesTableCompanion sale,
    required List<LocalSaleItemsTableCompanion> items,
    required List<
            ({
              String itemId,
              List<LocalSaleItemOptionsTableCompanion> opts,
              List<LocalSaleItemAddonsTableCompanion> addons,
            })>
        itemOptions,
    required List<LocalPaymentsTableCompanion> payments,
  }) async {
    await transaction(() async {
      await into(localSalesTable).insert(sale);
      await batch((b) {
        b.insertAll(localSaleItemsTable, items);
        for (final entry in itemOptions) {
          b.insertAll(localSaleItemOptionsTable, entry.opts);
          b.insertAll(localSaleItemAddonsTable, entry.addons);
        }
        b.insertAll(localPaymentsTable, payments);
      });
    });
  }

  /// Returns all items belonging to the sale with [saleId].
  Future<List<LocalSaleItemsTableData>> itemsForSale(String saleId) =>
      (select(localSaleItemsTable)..where((t) => t.saleId.equals(saleId)))
          .get();

  /// Returns all selected Variant Options for the sale item with [saleItemId].
  Future<List<LocalSaleItemOptionsTableData>> optionsForItem(
          String saleItemId) =>
      (select(localSaleItemOptionsTable)
            ..where((t) => t.saleItemId.equals(saleItemId)))
          .get();

  /// Returns all selected Add-ons for the sale item with [saleItemId].
  Future<List<LocalSaleItemAddonsTableData>> addonsForItem(String saleItemId) =>
      (select(localSaleItemAddonsTable)
            ..where((t) => t.saleItemId.equals(saleItemId)))
          .get();

  /// Returns all payment tenders for the sale with [saleId].
  Future<List<LocalPaymentsTableData>> paymentsForSale(String saleId) =>
      (select(localPaymentsTable)..where((t) => t.saleId.equals(saleId))).get();

  /// Marks the given [saleIds] as synced after a successful upload.
  ///
  /// Uses a bulk WHERE IN update rather than individual writes to minimize
  /// DB round-trips when a large offline batch is uploaded.
  Future<void> markSynced(List<String> saleIds) async {
    await (update(localSalesTable)..where((t) => t.id.isIn(saleIds)))
        .write(const LocalSalesTableCompanion(synced: Value(true)));
  }

  /// Quarantines [saleId] after a deterministic (non-retryable) server
  /// rejection — see [unsynced]'s doc comment for why this stops the
  /// perpetual-retry loop instead of leaving the row to fail identically on
  /// every future sync tick.
  Future<void> markNeedsReview(String saleId, String error) async {
    await (update(localSalesTable)..where((t) => t.id.equals(saleId))).write(
        LocalSalesTableCompanion(
            needsReview: const Value(true), syncError: Value(error)));
  }
}
