import 'package:drift/drift.dart';
import '../app_database.dart';
import '../tables/local_sales_table.dart';

part 'sync_dao.g.dart';

/// DAO focused on reactive sync-state queries for the offline outbox.
///
/// Kept separate from [SaleDao] because its sole purpose is exposing
/// a live count of unsynced sales — used to drive the outbox badge in the UI
/// without loading full sale records.
@DriftAccessor(tables: [LocalSalesTable])
class SyncDao extends DatabaseAccessor<AppDatabase> with _$SyncDaoMixin {
  SyncDao(super.db);

  /// Returns a stream that emits the current unsynced sale count whenever
  /// the [LocalSalesTable] changes.
  ///
  /// The UI subscribes to this stream to keep the outbox badge up to date
  /// in real time as sales are queued or uploaded.
  Stream<int> watchUnsyncedCount() {
    final q = selectOnly(localSalesTable)
      ..addColumns([localSalesTable.id.count()])
      ..where(localSalesTable.synced.equals(false));
    return q.map((row) => row.read(localSalesTable.id.count()) ?? 0).watchSingle();
  }

  /// Returns the current count of unsynced sales as a one-shot future.
  ///
  /// Used during upload to decide whether a batch upload is worth attempting.
  Future<int> unsyncedCount() async {
    final q = selectOnly(localSalesTable)
      ..addColumns([localSalesTable.id.count()])
      ..where(localSalesTable.synced.equals(false));
    final row = await q.getSingle();
    return row.read(localSalesTable.id.count()) ?? 0;
  }
}
