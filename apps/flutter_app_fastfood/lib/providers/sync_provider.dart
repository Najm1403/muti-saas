import 'package:riverpod_annotation/riverpod_annotation.dart';

import 'database_provider.dart';

part 'sync_provider.g.dart';

/// Live count of offline sales waiting to be uploaded.
///
/// Emits a new value whenever the [LocalSalesTable] changes, so the outbox
/// badge in the UI stays current without polling. Returns 0 when no DB exists.
@riverpod
Stream<int> unsyncedCount(UnsyncedCountRef ref) =>
    ref.watch(appDatabaseProvider).syncDao.watchUnsyncedCount();

/// Timestamp of the last successful sync from the cloud catalog.
///
/// Returns null on first launch (no sync has happened yet).
/// Used by the sync status indicator in settings or the app bar.
@riverpod
Future<DateTime?> lastSyncAt(LastSyncAtRef ref) =>
    ref.watch(appDatabaseProvider).settingsDao.getLastSyncAt();
