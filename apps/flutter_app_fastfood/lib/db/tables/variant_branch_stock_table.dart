import 'package:drift/drift.dart';

/// Per-branch quantity cache for tracked Variants (spec D2). The POS only
/// ever syncs the one branch its device is activated to, but the table is
/// keyed the same way as the server's VariantBranchStock so the shape — and
/// the option of a future multi-branch view — stays honest.
class VariantBranchStockTable extends Table {
  @override
  String get tableName => 'variant_branch_stock';

  TextColumn get variantId => text().named('variant_id')();
  TextColumn get branchId => text().named('branch_id')();
  IntColumn get quantity => integer().withDefault(const Constant(0))();

  @override
  Set<Column> get primaryKey => {variantId, branchId};
}
