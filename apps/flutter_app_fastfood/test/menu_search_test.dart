import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fastfood_pos/db/app_database.dart';

void main() {
  late AppDatabase db;

  setUp(() => db = AppDatabase.forTesting(NativeDatabase.memory()));
  tearDown(() => db.close());

  test('multi-word search matches combined variant group and value names',
      () async {
    await db.menuDao.upsertCategories([
      CategoriesTableCompanion.insert(
        id: 'c1',
        name: 'Computers',
        displayOrder: 0,
        isActive: true,
      ),
    ]);
    await db.menuDao.upsertProducts([
      ProductsTableCompanion.insert(
        id: 'p1',
        categoryId: 'c1',
        productCode: 'LAP-1',
        name: 'Work Laptop',
        basePrice: '1000.00',
        displayOrder: 0,
        isActive: true,
      ),
    ]);
    await db.menuDao.upsertVariantOptionGroups([
      VariantOptionGroupsTableCompanion.insert(
        id: 'g1',
        productId: 'p1',
        name: 'RAM',
        isRequired: true,
        displayOrder: 0,
      ),
    ]);
    await db.menuDao.upsertVariantOptions([
      VariantOptionsTableCompanion.insert(
        id: 'o1',
        optionGroupId: 'g1',
        name: '4 GB',
        displayOrder: 0,
        isActive: true,
      ),
    ]);
    await db.menuDao.upsertVariants([
      VariantsTableCompanion.insert(
        id: 'v1',
        productId: 'p1',
        optionValueIds: '["o1"]',
        salePrice: '1000.00',
        productName: const Value('Work Laptop'),
        variantName: const Value('RAM: 4 GB'),
      ),
    ]);

    expect((await db.menuDao.searchProducts('4 GB RAM')).single.id, 'p1');
    expect((await db.menuDao.searchProducts('work 4gb')).single.id, 'p1');
  });

  test('standalone component product gets its qualified picker name', () async {
    await db.menuDao.upsertVariants([
      VariantsTableCompanion.insert(
        id: 'component-v1',
        productId: 'ram-product',
        optionValueIds: '[]',
        salePrice: '2200.00',
      ),
    ]);
    await db.menuDao.upsertVariantOptionGroups([
      VariantOptionGroupsTableCompanion.insert(
        id: 'ram-group',
        productId: 'laptop-product',
        name: 'RAM',
        isRequired: true,
        displayOrder: 0,
        usageType: const Value('inventory_component'),
      ),
    ]);
    await db.menuDao.upsertVariantOptions([
      VariantOptionsTableCompanion.insert(
        id: 'ram-4gb',
        optionGroupId: 'ram-group',
        name: '4 GB',
        displayOrder: 0,
        isActive: true,
        componentVariantId: const Value('component-v1'),
      ),
    ]);

    expect(
      await db.menuDao.componentDisplayNameForProduct('ram-product'),
      'RAM: 4 GB',
    );
  });
}
