import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../db/app_database.dart';

part 'database_provider.g.dart';

/// Singleton Drift database. keepAlive so the connection is never closed.
@Riverpod(keepAlive: true)
AppDatabase appDatabase(AppDatabaseRef ref) {
  final db = AppDatabase();
  ref.onDispose(db.close);
  return db;
}

/// SharedPreferences instance for persisting non-sensitive device metadata
/// (device_id, branch_id, tenant_id, device_name) after activation.
@Riverpod(keepAlive: true)
Future<SharedPreferences> sharedPrefs(SharedPrefsRef ref) =>
    SharedPreferences.getInstance();
