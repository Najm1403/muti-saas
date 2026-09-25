// main_web_preview.dart
//
// Web entry point for previewing the POS screen on Chrome.
// Overrides all Drift/SQLite providers with hardcoded mock data so
// dart:ffi is never imported and the app runs cleanly on the web.
//
// Run with:
//   flutter run -d chrome -t lib/main_web_preview.dart

import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'db/app_database.dart';
import 'features/pos/pos_screen.dart';
import 'providers/menu_provider.dart';

// ---------------------------------------------------------------------------
// Mock menu data
// ---------------------------------------------------------------------------

const _cats = [
  CategoriesTableData(
      id: 'c1', name: 'Burgers', displayOrder: 1, isActive: true),
  CategoriesTableData(id: 'c2', name: 'Sides', displayOrder: 2, isActive: true),
  CategoriesTableData(
      id: 'c3', name: 'Drinks', displayOrder: 3, isActive: true),
  CategoriesTableData(
      id: 'c4', name: 'Desserts', displayOrder: 4, isActive: true),
  CategoriesTableData(
      id: 'c5', name: 'Breakfast', displayOrder: 5, isActive: true),
];

const _products = [
  ProductsTableData(
      id: 'p1',
      categoryId: 'c1',
      productCode: 'B001',
      name: 'Classic Burger',
      basePrice: '8.99',
      displayOrder: 1,
      isActive: true,
      trackInventory: false,
      allowNegativeStock: false),
  ProductsTableData(
      id: 'p2',
      categoryId: 'c1',
      productCode: 'B002',
      name: 'Cheese Burger',
      basePrice: '9.99',
      displayOrder: 2,
      isActive: true,
      trackInventory: false,
      allowNegativeStock: false),
  ProductsTableData(
      id: 'p3',
      categoryId: 'c1',
      productCode: 'B003',
      name: 'BBQ Burger',
      basePrice: '11.99',
      displayOrder: 3,
      isActive: true,
      trackInventory: false,
      allowNegativeStock: false),
  ProductsTableData(
      id: 'p4',
      categoryId: 'c1',
      productCode: 'B004',
      name: 'Veggie Burger',
      basePrice: '10.49',
      displayOrder: 4,
      isActive: true,
      trackInventory: false,
      allowNegativeStock: false),
  ProductsTableData(
      id: 'p5',
      categoryId: 'c2',
      productCode: 'S001',
      name: 'French Fries',
      basePrice: '3.49',
      displayOrder: 1,
      isActive: true,
      trackInventory: false,
      allowNegativeStock: false),
  ProductsTableData(
      id: 'p6',
      categoryId: 'c2',
      productCode: 'S002',
      name: 'Onion Rings',
      basePrice: '3.99',
      displayOrder: 2,
      isActive: true,
      trackInventory: false,
      allowNegativeStock: false),
  ProductsTableData(
      id: 'p7',
      categoryId: 'c2',
      productCode: 'S003',
      name: 'Coleslaw',
      basePrice: '2.49',
      displayOrder: 3,
      isActive: true,
      trackInventory: false,
      allowNegativeStock: false),
  ProductsTableData(
      id: 'p8',
      categoryId: 'c3',
      productCode: 'D001',
      name: 'Coca-Cola',
      basePrice: '2.49',
      displayOrder: 1,
      isActive: true,
      trackInventory: false,
      allowNegativeStock: false),
  ProductsTableData(
      id: 'p9',
      categoryId: 'c3',
      productCode: 'D002',
      name: 'Lemonade',
      basePrice: '2.99',
      displayOrder: 2,
      isActive: true,
      trackInventory: false,
      allowNegativeStock: false),
  ProductsTableData(
      id: 'p10',
      categoryId: 'c3',
      productCode: 'D003',
      name: 'Milkshake',
      basePrice: '4.99',
      displayOrder: 3,
      isActive: true,
      trackInventory: false,
      allowNegativeStock: false),
  ProductsTableData(
      id: 'p11',
      categoryId: 'c4',
      productCode: 'X001',
      name: 'Ice Cream',
      basePrice: '3.49',
      displayOrder: 1,
      isActive: true,
      trackInventory: false,
      allowNegativeStock: false),
  ProductsTableData(
      id: 'p12',
      categoryId: 'c4',
      productCode: 'X002',
      name: 'Brownie',
      basePrice: '2.99',
      displayOrder: 2,
      isActive: true,
      trackInventory: false,
      allowNegativeStock: false),
  ProductsTableData(
      id: 'p13',
      categoryId: 'c5',
      productCode: 'BR01',
      name: 'Pancakes',
      basePrice: '6.99',
      displayOrder: 1,
      isActive: true,
      trackInventory: false,
      allowNegativeStock: false),
  ProductsTableData(
      id: 'p14',
      categoryId: 'c5',
      productCode: 'BR02',
      name: 'Egg & Toast',
      basePrice: '5.49',
      displayOrder: 2,
      isActive: true,
      trackInventory: false,
      allowNegativeStock: false),
];

// p1 has a "Size" Variant Option Group (3 options) — 3 composed Variants.
// p2 has a "Size" Variant Option Group (2 options) — 2 composed Variants.
// Every other product sells through its own zero-option default Variant.
const _variantGroups = {
  'p1': [
    VariantOptionGroupsTableData(
        id: 'g1',
        productId: 'p1',
        name: 'Size',
        isRequired: true,
        displayOrder: 1,
        usageType: 'specification',
        allowedOptionIds: '[]'),
  ],
  'p2': [
    VariantOptionGroupsTableData(
        id: 'g3',
        productId: 'p2',
        name: 'Size',
        isRequired: true,
        displayOrder: 1,
        usageType: 'specification',
        allowedOptionIds: '[]'),
  ],
};

const _variantOptions = {
  'g1': [
    VariantOptionsTableData(
        id: 'o1',
        optionGroupId: 'g1',
        name: 'Regular',
        displayOrder: 1,
        isActive: true),
    VariantOptionsTableData(
        id: 'o2',
        optionGroupId: 'g1',
        name: 'Large',
        displayOrder: 2,
        isActive: true),
    VariantOptionsTableData(
        id: 'o3',
        optionGroupId: 'g1',
        name: 'XL',
        displayOrder: 3,
        isActive: true),
  ],
  'g3': [
    VariantOptionsTableData(
        id: 'o7',
        optionGroupId: 'g3',
        name: 'Regular',
        displayOrder: 1,
        isActive: true),
    VariantOptionsTableData(
        id: 'o8',
        optionGroupId: 'g3',
        name: 'Large',
        displayOrder: 2,
        isActive: true),
  ],
};

VariantsTableData _variant(String id, String productId, List<String> optionIds,
        String salePrice, bool isDefault) =>
    VariantsTableData(
      id: id,
      productId: productId,
      optionValueIds: jsonEncode(optionIds),
      salePrice: salePrice,
      tracksInventory: false,
      isDefault: isDefault,
      sellable: true,
      allowInventoryTracking: false,
    );

final _variants = {
  'p1': [
    _variant('v1', 'p1', ['o1'], '8.99', true),
    _variant('v2', 'p1', ['o2'], '10.49', false),
    _variant('v3', 'p1', ['o3'], '11.49', false),
  ],
  'p2': [
    _variant('v4', 'p2', ['o7'], '9.99', true),
    _variant('v5', 'p2', ['o8'], '11.49', false),
  ],
  for (final p in _products.where((p) => p.id != 'p1' && p.id != 'p2'))
    p.id: [_variant('v-${p.id}', p.id, const [], p.basePrice, true)],
};

const _addonGroups = {
  'p1': [
    AddonGroupsTableData(
        id: 'a1',
        productId: 'p1',
        name: 'Extras',
        selectionType: 'multiple',
        minSelect: 0,
        maxSelect: 3,
        displayOrder: 1),
  ],
};

const _addonItems = {
  'a1': [
    AddonItemsTableData(
        id: 'ai1',
        addonGroupId: 'a1',
        name: 'Extra Cheese',
        priceDelta: '0.75',
        defaultSelected: false,
        displayOrder: 1,
        isActive: true),
    AddonItemsTableData(
        id: 'ai2',
        addonGroupId: 'a1',
        name: 'Bacon',
        priceDelta: '1.25',
        defaultSelected: false,
        displayOrder: 2,
        isActive: true),
    AddonItemsTableData(
        id: 'ai3',
        addonGroupId: 'a1',
        name: 'Avocado',
        priceDelta: '1.00',
        defaultSelected: false,
        displayOrder: 3,
        isActive: true),
  ],
};

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------

void main() {
  runApp(
    ProviderScope(
      overrides: [
        // ── Flat providers ──────────────────────────────────────────────────
        categoriesProvider.overrideWith((ref) => Future.value([..._cats])),
        allActiveProductsProvider
            .overrideWith((ref) => Future.value([..._products])),

        // ── Family providers: override one instance per known ID ───────────
        // Products per category
        for (final cat in _cats)
          productsByCategoryProvider(cat.id).overrideWith(
            (ref) => Future.value(
              _products.where((p) => p.categoryId == cat.id).toList(),
            ),
          ),

        // Variant Option Groups + Options per product/group
        for (final product in _products)
          variantOptionGroupsProvider(product.id).overrideWith(
              (ref) => Future.value([...?_variantGroups[product.id]])),
        for (final entry in _variantOptions.entries)
          variantOptionsForGroupProvider(entry.key)
              .overrideWith((ref) => Future.value([...entry.value])),

        // Composed Variants per product
        for (final product in _products)
          variantsForProductProvider(product.id)
              .overrideWith((ref) => Future.value([...?_variants[product.id]])),

        // Add-on Groups + Items per product/group
        for (final product in _products)
          addonGroupsProvider(product.id).overrideWith(
              (ref) => Future.value([...?_addonGroups[product.id]])),
        for (final entry in _addonItems.entries)
          addonItemsForGroupProvider(entry.key)
              .overrideWith((ref) => Future.value([...entry.value])),
      ],
      child: const _PreviewApp(),
    ),
  );
}

class _PreviewApp extends StatelessWidget {
  const _PreviewApp();

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'POS Preview',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFFE65100)),
        useMaterial3: true,
      ),
      home: const PosScreen(),
    );
  }
}
