import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fastfood_pos/db/app_database.dart';

void main() {
  test('low stock counts only inventory-eligible variants for this branch',
      () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);

    VariantsTableCompanion variant(
      String id, {
      bool tracks = true,
      bool productAllows = true,
    }) =>
        VariantsTableCompanion.insert(
          id: id,
          productId: 'product-$id',
          optionValueIds: '[]',
          salePrice: '10.00',
          tracksInventory: Value(tracks),
          allowInventoryTracking: Value(productAllows),
        );

    await db.menuDao.upsertVariants([
      variant('missing-is-zero'),
      variant('low'),
      variant('healthy'),
      variant('variant-untracked', tracks: false),
      variant('product-untracked', productAllows: false),
    ]);
    await db.menuDao.upsertVariantBranchStock([
      VariantBranchStockTableCompanion.insert(
        variantId: 'low',
        branchId: 'branch-a',
        quantity: const Value(5),
      ),
      VariantBranchStockTableCompanion.insert(
        variantId: 'healthy',
        branchId: 'branch-a',
        quantity: const Value(6),
      ),
      VariantBranchStockTableCompanion.insert(
        variantId: 'variant-untracked',
        branchId: 'branch-a',
        quantity: const Value(0),
      ),
      VariantBranchStockTableCompanion.insert(
        variantId: 'product-untracked',
        branchId: 'branch-a',
        quantity: const Value(0),
      ),
    ]);

    expect(await db.menuDao.lowStockCount('branch-a', 5), 2);
    expect(await db.menuDao.lowStockCount('branch-a', 0), 1);
  });

  test('tenant low stock threshold is cached for offline use', () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    expect(await db.settingsDao.getLowStockThreshold(), 5);
    await db.settingsDao.setLowStockThreshold(12);
    expect(await db.settingsDao.getLowStockThreshold(), 12);
  });
}
