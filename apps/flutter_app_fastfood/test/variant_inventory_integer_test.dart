import 'package:fastfood_pos/core/models/sync/pos_sync_product.dart';
import 'package:drift/drift.dart' hide isNull;
import 'package:drift/native.dart';
import 'package:decimal/decimal.dart';
import 'package:fastfood_pos/db/app_database.dart';
import 'package:fastfood_pos/features/sale/cart_service.dart';
import 'package:fastfood_pos/features/sale/variant_inventory.dart';
import 'package:flutter_test/flutter_test.dart';

const _branchId = 'branch-1';

CartItem item(String id, Decimal quantity, {String variantId = 'v1'}) =>
    CartItem(
      id: id,
      variantId: variantId,
      productId: 'product-1',
      productName: 'Item',
      unitPrice: Decimal.fromInt(10),
      quantity: quantity,
    );

Future<void> _seedVariant(
  AppDatabase db, {
  String id = 'v1',
  bool allowInventoryTracking = true,
  bool tracksInventory = true,
  bool sellable = true,
  int stock = 5,
}) async {
  await db.menuDao.upsertVariants([
    VariantsTableCompanion.insert(
      id: id,
      productId: 'product-1',
      optionValueIds: '[]',
      salePrice: '10.00',
      allowInventoryTracking: Value(allowInventoryTracking),
      tracksInventory: Value(tracksInventory),
      sellable: Value(sellable),
    ),
  ]);
  await db.menuDao.setBranchStock(id, _branchId, stock);
}

void main() {
  test('product sync serializer uses the master tracking switch', () {
    final product = PosSyncProduct.fromJson({
      'id': 'p1',
      'category_id': 'c1',
      'product_code': 'P1',
      'name': 'Laptop',
      'price': '10.00',
      'display_order': 0,
      'is_active': true,
      'allow_inventory_tracking': true,
    });
    expect(product.allowInventoryTracking, isTrue);
    expect(product.toJson()['allow_inventory_tracking'], isTrue);
    expect(product.toJson().containsKey('track_inventory'), isFalse);
  });

  test('duplicate lines aggregate before validating stock', () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    await _seedVariant(db, stock: 5);
    final inventory = VariantInventory(db);
    final cart = CartSnapshot(
        items: [item('a', Decimal.fromInt(3)), item('b', Decimal.fromInt(3))],
        payments: const []);
    final demand = inventory.demandByVariant(cart);
    expect(demand, {'v1': 6});
    await expectLater(inventory.validateDemand(demand), throwsStateError);
  });

  test('selection requires a composed variant and counts cart demand', () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    await _seedVariant(db, stock: 5);
    final inventory = VariantInventory(db);
    final cart = CartSnapshot(
        items: [item('a', Decimal.fromInt(3))], payments: const []);
    expect(await inventory.selectionError('missing', 1, cart),
        contains('Sync to see variant availability'));
    expect(await inventory.selectionError('v1', 2, cart), isNull);
    expect(await inventory.selectionError('v1', 3, cart),
        contains('5 available, 6 requested'));

    await _seedVariant(db, id: 'v2', allowInventoryTracking: false, stock: 100);
    expect(await inventory.selectionError('v2', 100, cart), isNull);
  });

  test('either disabled toggle skips stock checks', () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    await _seedVariant(db, id: 'v-a', allowInventoryTracking: false, stock: 1);
    await _seedVariant(db, id: 'v-b', tracksInventory: false, stock: 1);
    final inventory = VariantInventory(db);
    for (final id in ['v-a', 'v-b']) {
      await expectLater(
          inventory.validateDemand({id: 999999}), completes);
    }
  });

  test('reservation is independent and rolls back with failed sale', () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    await _seedVariant(db, id: 'v1', stock: 5);
    await _seedVariant(db, id: 'v2', stock: 9);
    final inventory = VariantInventory(db);
    final cart = CartSnapshot(
        items: [item('a', Decimal.fromInt(2))], payments: const []);
    await expectLater(db.transaction(() async {
      await inventory.reserve(cart);
      throw StateError('Persistence failed');
    }), throwsStateError);
    expect((await db.menuDao.branchStockForVariant('v1'))!.quantity, 5);
    await db.transaction(() => inventory.reserve(cart));
    expect((await db.menuDao.branchStockForVariant('v1'))!.quantity, 3);
    expect((await db.menuDao.branchStockForVariant('v2'))!.quantity, 9);
  });

  test('confirmed sale honors product gate and never consumes other variants',
      () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    await _seedVariant(db, id: 'v1', allowInventoryTracking: false, stock: 5);
    await _seedVariant(db, id: 'v2', stock: 9);
    final inventory = VariantInventory(db);
    final cart = CartSnapshot(
        items: [item('a', Decimal.fromInt(20))], payments: const []);
    await inventory.consumeConfirmed(cart);
    expect((await db.menuDao.branchStockForVariant('v1'))!.quantity, 5);
    expect((await db.menuDao.branchStockForVariant('v2'))!.quantity, 9);
  });

  test('cart serialization rejects fractional quantities', () {
    final cart = CartSnapshot(
        items: [item('a', Decimal.parse('1.5'))], payments: const []);
    expect(() => cart.toPosSaleCreate(id: 's1', saleNumber: 'S1'),
        throwsStateError);
  });
}
