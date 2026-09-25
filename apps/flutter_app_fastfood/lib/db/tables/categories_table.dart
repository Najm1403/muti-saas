import 'package:drift/drift.dart';

/// Drift table definition for product categories synced from the cloud.
///
/// Data flows one way: cloud → tablet via [SyncRepository]. Rows are never
/// created or modified locally — only upserted during full/delta sync.
class CategoriesTable extends Table {
  @override
  String get tableName => 'categories';

  TextColumn get id => text()();
  TextColumn get name => text()();
  TextColumn get description => text().nullable()();
  TextColumn get imagePath => text().nullable().named('image_path')();
  IntColumn get displayOrder => integer().named('display_order')();
  BoolColumn get isActive => boolean().named('is_active')();

  @override
  Set<Column> get primaryKey => {id};
}
