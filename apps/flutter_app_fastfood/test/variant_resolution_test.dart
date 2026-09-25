// Verifies the shared POS resolution/pricing/stock-check logic
// (lib/features/pos/variant_resolution.dart) that BOTH POS layouts
// (grid_with_variant_picker's VariantContent and grid_quick_tap's instant-add
// + bottom sheet) call — this is the single source of truth these tests hold
// to spec's verification checklist.

import 'package:decimal/decimal.dart';
import 'package:drift/drift.dart' show Value;
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fastfood_pos/db/app_database.dart';
import 'package:fastfood_pos/features/pos/variant_resolution.dart';
import 'package:fastfood_pos/features/sale/cart_service.dart';
import 'package:fastfood_pos/features/sale/variant_inventory.dart';

VariantOptionGroupsTableData _group(String id,
        {bool required = true, String usageType = 'specification'}) =>
    VariantOptionGroupsTableData(
        id: id,
        productId: 'p1',
        name: 'Size',
        isRequired: required,
        displayOrder: 0,
        usageType: usageType,
        allowedOptionIds: '[]');

VariantsTableData _variant(
  String id, {
  required List<String> optionIds,
  required String salePrice,
  bool tracksInventory = false,
  bool isDefault = false,
  bool sellable = true,
  bool allowInventoryTracking = false,
}) =>
    VariantsTableData(
      id: id,
      productId: 'p1',
      optionValueIds: '[${optionIds.map((e) => '"$e"').join(',')}]',
      salePrice: salePrice,
      tracksInventory: tracksInventory,
      isDefault: isDefault,
      sellable: sellable,
      allowInventoryTracking: allowInventoryTracking,
    );

AddonGroupsTableData _addonGroup(String id) => AddonGroupsTableData(
    id: id,
    productId: 'p1',
    name: 'Toppings',
    selectionType: 'multiple',
    minSelect: 0,
    displayOrder: 0);

AddonItemsTableData _addonItem(String id, String groupId, String priceDelta,
        {bool defaultSelected = false}) =>
    AddonItemsTableData(
      id: id,
      addonGroupId: groupId,
      name: 'Item $id',
      priceDelta: priceDelta,
      defaultSelected: defaultSelected,
      displayOrder: 0,
      isActive: true,
    );

CartSnapshot _emptyCart() => CartSnapshot(items: const [], payments: const []);

void main() {
  group('resolveSelectedVariant — checklist items 1 & 2', () {
    final group = _group('g1');
    final small =
        _variant('v-small', optionIds: ['opt-small'], salePrice: '5.00');
    final large =
        _variant('v-large', optionIds: ['opt-large'], salePrice: '8.00');

    test(
        'a different selection resolves to a different Variant with a different price',
        () {
      final atSmall = resolveSelectedVariant(
        groups: [group],
        variants: [small, large],
        selectedVariantOptions: {'g1': 'opt-small'},
      );
      final atLarge = resolveSelectedVariant(
        groups: [group],
        variants: [small, large],
        selectedVariantOptions: {'g1': 'opt-large'},
      );
      expect(atSmall!.salePrice, '5.00');
      expect(atLarge!.salePrice, '8.00');
      expect(atSmall.id, isNot(atLarge.id));
    });

    test(
        'a combination with no matching synced Variant resolves to null — never a stale price',
        () {
      final resolved = resolveSelectedVariant(
        groups: [group],
        variants: [small, large],
        selectedVariantOptions: {'g1': 'opt-medium-does-not-exist'},
      );
      expect(resolved, isNull);
    });

    test('an incomplete selection (group unanswered) resolves to null', () {
      final resolved = resolveSelectedVariant(
        groups: [group],
        variants: [small, large],
        selectedVariantOptions: const {},
      );
      expect(resolved, isNull);
    });

    test('a zero-group product always resolves to its default variant', () {
      final theOnlyVariant = _variant('v-default',
          optionIds: const [], salePrice: '3.50', isDefault: true);
      final resolved = resolveSelectedVariant(
        groups: const [],
        variants: [theOnlyVariant],
        selectedVariantOptions: const {},
      );
      expect(resolved!.id, 'v-default');
    });
  });

  group('resolveAddonsDelta — checklist item 4', () {
    final group = _addonGroup('ag1');
    final cheese = _addonItem('cheese', 'ag1', '100');
    final olives = _addonItem('olives', 'ag1', '80');
    final itemsByGroup = {
      'ag1': [cheese, olives]
    };

    test(
        'toggling an add-on changes the total on the very next call — no caching',
        () {
      final before = resolveAddonsDelta(
        addonGroups: [group],
        selectedAddons: const {},
        itemsByGroup: itemsByGroup,
      );
      expect(before, Decimal.zero);

      final afterCheese = resolveAddonsDelta(
        addonGroups: [group],
        selectedAddons: {
          'ag1': {'cheese'}
        },
        itemsByGroup: itemsByGroup,
      );
      expect(afterCheese, Decimal.parse('100'));

      final afterBoth = resolveAddonsDelta(
        addonGroups: [group],
        selectedAddons: {
          'ag1': {'cheese', 'olives'}
        },
        itemsByGroup: itemsByGroup,
      );
      expect(afterBoth, Decimal.parse('180'));

      // Unchecking is reflected immediately too — no stale total left over.
      final afterUncheckCheese = resolveAddonsDelta(
        addonGroups: [group],
        selectedAddons: {
          'ag1': {'olives'}
        },
        itemsByGroup: itemsByGroup,
      );
      expect(afterUncheckCheese, Decimal.parse('80'));
    });
  });

  group('productNeedsPicker — checklist item 6, decided per-product only', () {
    test(
        'a product with only its default variant and no add-ons never needs a picker',
        () {
      final theOnlyVariant =
          _variant('v-default', optionIds: const [], salePrice: '3.50');
      expect(
        productNeedsPicker(variants: [theOnlyVariant], addonGroups: const []),
        isFalse,
      );
    });

    test('a product with real Variant Option combinations needs the picker',
        () {
      final small =
          _variant('v-small', optionIds: ['opt-small'], salePrice: '5.00');
      final large =
          _variant('v-large', optionIds: ['opt-large'], salePrice: '8.00');
      expect(
        productNeedsPicker(variants: [small, large], addonGroups: const []),
        isTrue,
      );
    });

    test('a single-variant product with an Add-on Group still needs the picker',
        () {
      final theOnlyVariant =
          _variant('v-default', optionIds: const [], salePrice: '3.50');
      expect(
        productNeedsPicker(
          variants: [theOnlyVariant],
          addonGroups: [_addonGroup('ag1')],
        ),
        isTrue,
      );
    });
  });

  group('evaluateAddToCartStatus — checklist items 2, 3, 5 (canSell)', () {
    late AppDatabase db;
    setUp(() => db = AppDatabase.forTesting(NativeDatabase.memory()));
    tearDown(() => db.close());

    test(
        'incomplete selection is blocked with a distinct reason from out-of-stock',
        () async {
      final status = await evaluateAddToCartStatus(
        resolvedVariant: null,
        allGroupsSelected: false,
        quantity: 1,
        inventory: VariantInventory(db),
        cart: _emptyCart(),
      );
      expect(status.blocked, isTrue);
      expect(status.isIncompleteSelection, isTrue);
      expect(status.isOutOfStock, isFalse);
    });

    test(
        'a resolved, correctly-priced but out-of-stock Variant is blocked as out-of-stock, '
        'not incomplete-selection, and Add to Cart stays blocked', () async {
      await db.menuDao.upsertVariants([
        VariantsTableCompanion.insert(
          id: 'v1',
          productId: 'p1',
          optionValueIds: '[]',
          salePrice: '12.00',
          tracksInventory: const Value(true),
          allowInventoryTracking: const Value(true),
          sellable: const Value(true),
        ),
      ]);
      await db.menuDao.upsertVariantBranchStock([
        VariantBranchStockTableCompanion.insert(
            variantId: 'v1', branchId: 'b1', quantity: const Value(0)),
      ]);
      final variant = (await db.menuDao.variantById('v1'))!;

      final status = await evaluateAddToCartStatus(
        resolvedVariant: variant,
        allGroupsSelected: true,
        quantity: 1,
        inventory: VariantInventory(db),
        cart: _emptyCart(),
      );

      expect(status.blocked, isTrue);
      expect(status.isOutOfStock, isTrue, reason: status.message);
      expect(status.isIncompleteSelection, isFalse);
    });

    test('a resolved Variant with enough stock is ready to add', () async {
      await db.menuDao.upsertVariants([
        VariantsTableCompanion.insert(
          id: 'v2',
          productId: 'p1',
          optionValueIds: '[]',
          salePrice: '12.00',
          tracksInventory: const Value(true),
          allowInventoryTracking: const Value(true),
          sellable: const Value(true),
        ),
      ]);
      await db.menuDao.upsertVariantBranchStock([
        VariantBranchStockTableCompanion.insert(
            variantId: 'v2', branchId: 'b1', quantity: const Value(5)),
      ]);
      final variant = (await db.menuDao.variantById('v2'))!;

      final status = await evaluateAddToCartStatus(
        resolvedVariant: variant,
        allGroupsSelected: true,
        quantity: 1,
        inventory: VariantInventory(db),
        cart: _emptyCart(),
      );

      expect(status.blocked, isFalse);
    });
  });

  group('buildCartItem — single shared construction path', () {
    test(
        'builds display-only variant options and priced add-ons, including removed defaults',
        () {
      const product = ProductsTableData(
        id: 'p1',
        categoryId: 'c1',
        productCode: 'PZ',
        name: 'Pepperoni Pizza',
        basePrice: '9.00',
        displayOrder: 0,
        isActive: true,
        trackInventory: false,
        allowNegativeStock: false,
      );
      final group = _group('g1');
      final variant =
          _variant('v-med', optionIds: ['opt-medium'], salePrice: '11.00');
      const sizeOption = VariantOptionsTableData(
          id: 'opt-medium',
          optionGroupId: 'g1',
          name: 'Medium',
          displayOrder: 0,
          isActive: true);
      final addonGroup = _addonGroup('ag1');
      final onion = _addonItem('onion', 'ag1', '0', defaultSelected: true);
      final cheese = _addonItem('cheese', 'ag1', '100');

      final item = buildCartItem(
        product: product,
        variant: variant,
        groups: [group],
        selectedVariantOptions: {'g1': 'opt-medium'},
        optionsByGroup: {
          'g1': [sizeOption]
        },
        addonGroups: [addonGroup],
        // Cashier checked cheese, and explicitly unchecked the default-on onion.
        selectedAddons: {
          'ag1': {'cheese'}
        },
        addonItemsByGroup: {
          'ag1': [onion, cheese]
        },
        quantity: 2,
        id: 'line-1',
      );

      expect(item.variantId, 'v-med');
      expect(item.unitPrice, Decimal.parse('11.00'));
      expect(item.quantity, Decimal.fromInt(2));
      expect(item.variantOptions.single.optionName, 'Size: Medium');

      final cheeseLine =
          item.addons.firstWhere((a) => a.addonItemId == 'cheese');
      expect(cheeseLine.wasRemoved, isFalse);
      expect(cheeseLine.priceDelta, Decimal.parse('100'));

      final onionLine = item.addons.firstWhere((a) => a.addonItemId == 'onion');
      expect(onionLine.wasRemoved, isTrue,
          reason:
              'a default_selected item the cashier unchecked must be recorded as removed');

      // addonsTotal must exclude the removed default (spec F2).
      expect(item.addonsTotal, Decimal.parse('100'));
    });
  });

  group('Laptop Store shareable-inventory model — Component Groups', () {
    test('componentGroupsOf/specificationGroupsOf split by usage_type', () {
      final spec = _group('g1', usageType: 'specification');
      final component = _group('g2', usageType: 'inventory_component');
      final groups = [spec, component];

      expect(componentGroupsOf(groups), [component]);
      expect(specificationGroupsOf(groups), [spec]);
    });

    test(
        'a product with only its own default variant still needs the picker '
        'when it has an attached Inventory Component group', () {
      final theOnlyVariant =
          _variant('v-default', optionIds: const [], salePrice: '50000.00');
      final componentGroup = _group('g1', usageType: 'inventory_component');
      expect(
        productNeedsPicker(
          variants: [theOnlyVariant],
          addonGroups: const [],
          groups: [componentGroup],
        ),
        isTrue,
      );
      // Confirms the existing "no groups at all" case is genuinely why it
      // was false before — not some unrelated change.
      expect(
        productNeedsPicker(variants: [theOnlyVariant], addonGroups: const []),
        isFalse,
      );
    });

    test(
        'allowedComponentOptionIds: empty means unrestricted, non-empty is parsed',
        () {
      final unrestricted = _group('g1', usageType: 'inventory_component');
      expect(allowedComponentOptionIds(unrestricted), isEmpty);

      const restricted = VariantOptionGroupsTableData(
        id: 'g2',
        productId: 'p1',
        name: 'RAM',
        isRequired: true,
        displayOrder: 0,
        usageType: 'inventory_component',
        allowedOptionIds: '["opt-8gb","opt-16gb"]',
      );
      expect(allowedComponentOptionIds(restricted), ['opt-8gb', 'opt-16gb']);
    });

    test('allRequiredComponentsSelected: only required groups must have a pick',
        () {
      final required =
          _group('g1', usageType: 'inventory_component', required: true);
      final optional =
          _group('g2', usageType: 'inventory_component', required: false);
      final groups = [required, optional];

      expect(allRequiredComponentsSelected(groups, const {}), isFalse);
      expect(allRequiredComponentsSelected(groups, {'g1': 'opt-16gb'}), isTrue,
          reason:
              'the optional group having no pick must never block readiness');
      expect(allRequiredComponentsSelected(groups, {'g2': 'opt-x'}), isFalse,
          reason: 'picking the optional one does not satisfy the required one');
    });

    test(
        'resolveComponentsDelta sums only the currently-selected components\' own prices',
        () {
      final ramGroup = _group('g1', usageType: 'inventory_component');
      final ssdGroup = _group('g2', usageType: 'inventory_component');
      final ram16 = _variant('ram-16gb-variant',
          optionIds: const [], salePrice: '12000.00');
      final ssd512 = _variant('ssd-512-variant',
          optionIds: const [], salePrice: '15000.00');

      final noneSelected = resolveComponentsDelta(
        componentGroups: [ramGroup, ssdGroup],
        selectedComponents: const {},
        componentVariantByOptionId: const {},
      );
      expect(noneSelected, Decimal.zero);

      final bothSelected = resolveComponentsDelta(
        componentGroups: [ramGroup, ssdGroup],
        selectedComponents: {'g1': 'opt-ram16', 'g2': 'opt-ssd512'},
        componentVariantByOptionId: {'opt-ram16': ram16, 'opt-ssd512': ssd512},
      );
      expect(bothSelected, Decimal.parse('27000.00'));

      // A selection whose Variant hasn't resolved yet (still loading/null)
      // contributes nothing rather than throwing — matches the "fails open,
      // never stale/guessed" rule used throughout this file.
      final oneUnresolved = resolveComponentsDelta(
        componentGroups: [ramGroup, ssdGroup],
        selectedComponents: {'g1': 'opt-ram16', 'g2': 'opt-ssd512'},
        componentVariantByOptionId: {'opt-ram16': ram16, 'opt-ssd512': null},
      );
      expect(oneUnresolved, Decimal.parse('12000.00'));
    });

    test(
        'evaluateAddToCartStatus blocks as out-of-stock when the BASE variant is fine '
        'but a selected component has none', () async {
      final db = AppDatabase.forTesting(NativeDatabase.memory());
      addTearDown(db.close);

      await db.menuDao.upsertVariants([
        VariantsTableCompanion.insert(
          id: 'chassis-v1',
          productId: 'p1',
          optionValueIds: '[]',
          salePrice: '50000.00',
          tracksInventory: const Value(true),
          allowInventoryTracking: const Value(true),
          sellable: const Value(true),
        ),
        VariantsTableCompanion.insert(
          id: 'ram-v1',
          productId: 'p-ram',
          optionValueIds: '[]',
          salePrice: '12000.00',
          tracksInventory: const Value(true),
          allowInventoryTracking: const Value(true),
          sellable: const Value(true),
        ),
      ]);
      await db.menuDao.upsertVariantBranchStock([
        VariantBranchStockTableCompanion.insert(
            variantId: 'chassis-v1', branchId: 'b1', quantity: const Value(5)),
        VariantBranchStockTableCompanion.insert(
            variantId: 'ram-v1', branchId: 'b1', quantity: const Value(0)),
      ]);
      final chassis = (await db.menuDao.variantById('chassis-v1'))!;
      final ram = (await db.menuDao.variantById('ram-v1'))!;

      final status = await evaluateAddToCartStatus(
        resolvedVariant: chassis,
        allGroupsSelected: true,
        quantity: 1,
        inventory: VariantInventory(db),
        cart: _emptyCart(),
        selectedComponentVariants: [ram],
      );

      expect(status.blocked, isTrue);
      expect(status.isOutOfStock, isTrue, reason: status.message);
    });
  });

  group(
      'buildCartItems — base item plus one ordinary sibling per selected component',
      () {
    test(
        'a selected component is its own CartItem, tagged back to the base item',
        () {
      const product = ProductsTableData(
        id: 'p1',
        categoryId: 'c1',
        productCode: 'LAPTOP',
        name: 'Configurable Laptop',
        basePrice: '50000.00',
        displayOrder: 0,
        isActive: true,
        trackInventory: false,
        allowNegativeStock: false,
      );
      final chassisVariant =
          _variant('chassis-v1', optionIds: const [], salePrice: '50000.00');
      final ramGroup =
          _group('g1', usageType: 'inventory_component', required: true);
      const ramOption = VariantOptionsTableData(
        id: 'opt-ram16',
        optionGroupId: 'g1',
        name: '16GB DDR4',
        displayOrder: 0,
        isActive: true,
        componentVariantId: 'ram-v1',
      );
      const ramVariant = VariantsTableData(
        id: 'ram-v1',
        productId: 'p-ram',
        optionValueIds: '[]',
        salePrice: '12000.00',
        tracksInventory: false,
        isDefault: true,
        sellable: true,
        allowInventoryTracking: false,
        productName: 'RAM 16GB DDR4 Stick',
      );

      final items = buildCartItems(
        product: product,
        variant: chassisVariant,
        groups: const [],
        selectedVariantOptions: const {},
        optionsByGroup: const {},
        addonGroups: const [],
        selectedAddons: const {},
        addonItemsByGroup: const {},
        componentGroups: [ramGroup],
        selectedComponents: {'g1': 'opt-ram16'},
        componentOptionsById: {'opt-ram16': ramOption},
        componentVariantByOptionId: {'opt-ram16': ramVariant},
        quantity: 2,
        id: 'base-1',
      );

      expect(items, hasLength(2));
      final base = items[0];
      final component = items[1];

      expect(base.id, 'base-1');
      expect(base.variantId, 'chassis-v1');
      expect(base.parentCartItemId, isNull,
          reason: 'the base line is never itself tagged as a component');

      expect(component.variantId, 'ram-v1',
          reason:
              'the component resolves to its OWN Variant, never the chassis\'s');
      expect(component.productName, 'RAM 16GB DDR4 Stick');
      expect(component.unitPrice, Decimal.parse('12000.00'));
      expect(component.quantity, Decimal.fromInt(2),
          reason: 'buying 2 laptops means 2 of each selected component');
      expect(component.parentCartItemId, 'base-1');
      expect(component.satisfiesOptionGroupId, 'g1');
      expect(component.componentOptionId, 'opt-ram16');
      expect(
        component.id,
        matches(RegExp(
          r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
        )),
        reason: 'every submitted sale-item id must be a UUID',
      );
    });

    test('an unselected optional component group contributes no extra item',
        () {
      const product = ProductsTableData(
        id: 'p1',
        categoryId: 'c1',
        productCode: 'LAPTOP',
        name: 'Configurable Laptop',
        basePrice: '50000.00',
        displayOrder: 0,
        isActive: true,
        trackInventory: false,
        allowNegativeStock: false,
      );
      final chassisVariant =
          _variant('chassis-v1', optionIds: const [], salePrice: '50000.00');
      final ramGroup =
          _group('g1', usageType: 'inventory_component', required: false);

      final items = buildCartItems(
        product: product,
        variant: chassisVariant,
        groups: const [],
        selectedVariantOptions: const {},
        optionsByGroup: const {},
        addonGroups: const [],
        selectedAddons: const {},
        addonItemsByGroup: const {},
        componentGroups: [ramGroup],
        selectedComponents: const {},
        componentOptionsById: const {},
        componentVariantByOptionId: const {},
        quantity: 1,
        id: 'base-2',
      );

      expect(items, hasLength(1));
    });
  });
}
