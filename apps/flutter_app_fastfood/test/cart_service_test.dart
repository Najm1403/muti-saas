import 'package:decimal/decimal.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fastfood_pos/features/sale/cart_service.dart';

CartItem _item(String id, {String? parentCartItemId, String? variantId}) =>
    CartItem(
      id: id,
      variantId: variantId ?? 'v-$id',
      productId: 'p-$id',
      productName: 'Item $id',
      unitPrice: Decimal.fromInt(10),
      quantity: Decimal.one,
      parentCartItemId: parentCartItemId,
      satisfiesOptionGroupId: parentCartItemId == null ? null : 'group-1',
      componentOptionId: parentCartItemId == null ? null : 'option-1',
    );

void main() {
  group('CartService — Laptop Store shareable-inventory component cascade', () {
    test('adding repeated configured products keeps both parent links valid',
        () {
      final cart = CartService();
      final firstParent = _item('laptop-a', variantId: 'v-laptop');
      final secondParent = _item('laptop-b', variantId: 'v-laptop');

      cart.addItems([
        firstParent,
        _item('ram-a',
            parentCartItemId: firstParent.id, variantId: 'v-ram-4gb'),
      ]);
      cart.addItems([
        secondParent,
        _item('ram-b',
            parentCartItemId: secondParent.id, variantId: 'v-ram-4gb'),
      ]);

      expect(cart.items.length, 4);
      final parentIds = cart.items
          .where((item) => item.parentCartItemId == null)
          .map((item) => item.id)
          .toSet();
      final components =
          cart.items.where((item) => item.parentCartItemId != null);
      expect(components, hasLength(2));
      expect(
          components.every(
              (item) => parentIds.contains(item.parentCartItemId)),
          isTrue);
    });

    test('simple products still merge when added as a one-item bundle', () {
      final cart = CartService();
      cart.addItems([_item('simple-a', variantId: 'v-simple')]);
      cart.addItems([_item('simple-b', variantId: 'v-simple')]);

      expect(cart.items, hasLength(1));
      expect(cart.items.single.quantity, Decimal.fromInt(2));
    });

    test('removeItem also removes any component tagged to it', () {
      final cart = CartService();
      cart.addItem(_item('laptop'));
      cart.addItem(_item('ram', parentCartItemId: 'laptop'));
      cart.addItem(_item('unrelated-drink'));

      cart.removeItem('laptop');

      final remainingIds = cart.items.map((i) => i.id).toSet();
      expect(remainingIds, {'unrelated-drink'});
    });

    test('removeItem leaves other items and their own components untouched',
        () {
      final cart = CartService();
      cart.addItem(_item('laptop-a'));
      cart.addItem(_item('ram-a', parentCartItemId: 'laptop-a'));
      cart.addItem(_item('laptop-b'));
      cart.addItem(_item('ram-b', parentCartItemId: 'laptop-b'));

      cart.removeItem('laptop-a');

      final remainingIds = cart.items.map((i) => i.id).toSet();
      expect(remainingIds, {'laptop-b', 'ram-b'});
    });

    test('updateQuantity to zero cascades the same as removeItem', () {
      final cart = CartService();
      cart.addItem(_item('laptop'));
      cart.addItem(_item('ram', parentCartItemId: 'laptop'));

      cart.updateQuantity('laptop', Decimal.zero);

      expect(cart.items, isEmpty);
    });

    test('two components sharing a variant (e.g. both 16GB RAM) never merge',
        () {
      final cart = CartService();
      cart.addItem(_item('laptop-a'));
      cart.addItem(_item('ram-a',
          parentCartItemId: 'laptop-a', variantId: 'v-ram-16gb'));
      cart.addItem(_item('laptop-b'));
      cart.addItem(_item('ram-b',
          parentCartItemId: 'laptop-b', variantId: 'v-ram-16gb'));

      expect(cart.items.length, 4);
      expect(cart.items.where((i) => i.variantId == 'v-ram-16gb').length, 2);
    });
  });

  test('submission repairs legacy item IDs and preserves component linkage',
      () {
    final cart = CartService();
    cart.addItem(_item('legacy-parent'));
    cart.addItem(_item('legacy-component', parentCartItemId: 'legacy-parent'));

    final request = cart.snapshot().toPosSaleCreate(
          id: '27a704c8-2034-480a-a92e-12b623aa5c69',
          saleNumber: 'TEST-1',
        );

    final parent = request.items[0];
    final component = request.items[1];
    final uuid = RegExp(
      r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
    );

    expect(parent.id, matches(uuid));
    expect(component.id, matches(uuid));
    expect(component.parentItemId, parent.id);
  });

  test('submission rejects an orphaned component before calling the API', () {
    final cart = CartService();
    cart.addItem(_item('orphan', parentCartItemId: 'missing-parent'));

    expect(
      () => cart.snapshot().toPosSaleCreate(
            id: '27a704c8-2034-480a-a92e-12b623aa5c69',
            saleNumber: 'TEST-ORPHAN',
          ),
      throwsA(isA<StateError>().having(
          (error) => error.message, 'message', contains('orphaned component'))),
    );
  });
}
