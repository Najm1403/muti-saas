import 'package:drift/drift.dart';

/// Drift table for persistent key-value application settings.
///
/// Used for values that must survive app restarts but don't belong in a
/// dedicated table. Known keys are managed via typed accessors in [SettingsDao]:
/// - "last_sync_at" — ISO-8601 timestamp of the last successful sync
/// - "sale_counter" — monotonically increasing integer for sale number generation
class AppSettingsTable extends Table {
  @override
  String get tableName => 'app_settings';

  TextColumn get key => text()();
  TextColumn get value => text()();

  @override
  Set<Column> get primaryKey => {key};
}
