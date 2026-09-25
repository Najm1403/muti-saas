import 'dart:convert';

import 'package:drift/drift.dart';
import '../app_database.dart';
import '../tables/categories_table.dart';
import '../tables/products_table.dart';
import '../tables/variant_option_groups_table.dart';
import '../tables/variant_options_table.dart';
import '../tables/variants_table.dart';
import '../tables/variant_branch_stock_table.dart';
import '../tables/addon_groups_table.dart';
import '../tables/addon_items_table.dart';
import '../tables/deals_table.dart';
import '../tables/deal_items_table.dart';
import '../tables/promotions_table.dart';
import '../tables/local_product_stock_table.dart';

part 'menu_dao.g.dart';

/// DAO for all read and write operations on catalog tables.
///
/// Covers categories, products, Variant Option Groups/Options, composed
/// Variants + branch stock, Add-on Groups/Items, deals, deal items,
/// and promotions. All upsert methods use [insertAllOnConflictUpdate] so that
/// repeated full syncs are idempotent — existing rows are replaced, not
/// duplicated. No delete methods exist because catalog data is only removed by
/// the server marking records inactive ([isActive] = false), except the
/// per-sync-cycle tables ([VariantsTable], [VariantBranchStockTable])
/// which are fully replaced via [AppDatabase.clearCatalog]
/// since sync in this codebase is always a full replace (spec F5).
@DriftAccessor(tables: [
  CategoriesTable,
  ProductsTable,
  VariantOptionGroupsTable,
  VariantOptionsTable,
  VariantsTable,
  VariantBranchStockTable,
  AddonGroupsTable,
  AddonItemsTable,
  DealsTable,
  DealItemsTable,
  PromotionsTable,
  LocalProductStockTable,
])
class MenuDao extends DatabaseAccessor<AppDatabase> with _$MenuDaoMixin {
  MenuDao(super.db);

  // ── Categories ──────────────────────────────────────────────

  /// Returns all categories ordered by [displayOrder] ascending.
  Future<List<CategoriesTableData>> allCategories() => (select(categoriesTable)
        ..orderBy([(t) => OrderingTerm.asc(t.displayOrder)]))
      .get();

  /// Upserts [rows] into the categories table; existing rows are fully replaced.
  Future<void> upsertCategories(List<CategoriesTableCompanion> rows) =>
      batch((b) => b.insertAllOnConflictUpdate(categoriesTable, rows));

  // ── Products ─────────────────────────────────────────────────

  /// Returns all active products ordered by [displayOrder] ascending.
  Future<List<ProductsTableData>> activeProducts() => (select(productsTable)
        ..where((t) => t.isActive.equals(true))
        ..orderBy([(t) => OrderingTerm.asc(t.displayOrder)]))
      .get();

  /// Returns active products filtered to [categoryId], ordered by [displayOrder].
  Future<List<ProductsTableData>> productsByCategory(String categoryId) =>
      (select(productsTable)
            ..where((t) =>
                t.categoryId.equals(categoryId) & t.isActive.equals(true))
            ..orderBy([(t) => OrderingTerm.asc(t.displayOrder)]))
          .get();

  /// Upserts [rows] into the products table; existing rows are fully replaced.
  Future<void> upsertProducts(List<ProductsTableCompanion> rows) =>
      batch((b) => b.insertAllOnConflictUpdate(productsTable, rows));

  /// Active products whose product, option-group, option-value, or composed
  /// variant names match every word in [query] (case-insensitive).
  ///
  /// Spans every category — search intentionally ignores the current
  /// category selection. There is no locally-synced product_specs table, so
  /// spec key/value search is out of scope here. Done as three simple
  /// queries + a Dart-side merge rather than a SQL join, since the local
  /// catalog is small (a single tenant's product list) and this keeps each
  /// query trivially easy to verify against the existing DAO patterns above.
  Future<List<ProductsTableData>> searchProducts(String query) async {
    final needle = query.trim().toLowerCase();
    if (needle.isEmpty) return [];

    final products = await activeProducts();
    final groups = await select(variantOptionGroupsTable).get();
    final options = await select(variantOptionsTable).get();
    final variants = await select(variantsTable).get();

    final optionsByGroup = <String, List<VariantOptionsTableData>>{};
    for (final option in options) {
      optionsByGroup.putIfAbsent(option.optionGroupId, () => []).add(option);
    }
    final groupsByProduct = <String, List<VariantOptionGroupsTableData>>{};
    for (final group in groups) {
      groupsByProduct.putIfAbsent(group.productId, () => []).add(group);
    }
    final variantsByProduct = <String, List<VariantsTableData>>{};
    for (final variant in variants) {
      variantsByProduct.putIfAbsent(variant.productId, () => []).add(variant);
    }

    final terms = needle.split(RegExp(r'\s+')).where((t) => t.isNotEmpty);
    return products.where((product) {
      final searchable = <String>[
        product.name,
        product.productCode,
        for (final group in groupsByProduct[product.id] ?? const []) ...[
          group.name,
          for (final option in optionsByGroup[group.id] ?? const [])
            option.name,
        ],
        for (final variant in variantsByProduct[product.id] ?? const []) ...[
          variant.productName ?? '',
          variant.variantName ?? '',
          for (final optionId in (jsonDecode(variant.optionValueIds) as List))
            options
                    .cast<VariantOptionsTableData?>()
                    .firstWhere(
                      (option) => option?.id == optionId.toString(),
                      orElse: () => null,
                    )
                    ?.name ??
                '',
        ],
      ].join(' ').toLowerCase();
      final compactSearchable = searchable.replaceAll(RegExp(r'[^a-z0-9]'), '');
      return terms.every((term) =>
          searchable.contains(term) ||
          compactSearchable
              .contains(term.replaceAll(RegExp(r'[^a-z0-9]'), '')));
    }).toList();
  }

  // ── Variant Option Groups + Options ───────────────────────────

  /// Returns Variant Option Groups for [productId], ordered by [displayOrder].
  Future<List<VariantOptionGroupsTableData>> variantOptionGroupsForProduct(
          String productId) =>
      (select(variantOptionGroupsTable)
            ..where((t) => t.productId.equals(productId))
            ..orderBy([(t) => OrderingTerm.asc(t.displayOrder)]))
          .get();

  /// Returns active Variant Options for [groupId], ordered by [displayOrder].
  Future<List<VariantOptionsTableData>> variantOptionsForGroup(
          String groupId) =>
      (select(variantOptionsTable)
            ..where((t) =>
                t.optionGroupId.equals(groupId) & t.isActive.equals(true))
            ..orderBy([(t) => OrderingTerm.asc(t.displayOrder)]))
          .get();

  /// Upserts [rows] into variant_option_groups; existing rows are fully replaced.
  Future<void> upsertVariantOptionGroups(
          List<VariantOptionGroupsTableCompanion> rows) =>
      batch((b) => b.insertAllOnConflictUpdate(variantOptionGroupsTable, rows));

  /// Upserts [rows] into variant_options; existing rows are fully replaced.
  Future<void> upsertVariantOptions(List<VariantOptionsTableCompanion> rows) =>
      batch((b) => b.insertAllOnConflictUpdate(variantOptionsTable, rows));

  // ── Variants (composed SKUs) + branch stock ─────────

  /// Returns every synced Variant for [productId] — including non-default
  /// ones — in no particular order (the caller resolves by option combination).
  Future<List<VariantsTableData>> variantsForProduct(String productId) =>
      (select(variantsTable)..where((t) => t.productId.equals(productId)))
          .get();

  /// Returns the single Variant row with [variantId], or null if not synced.
  Future<VariantsTableData?> variantById(String variantId) =>
      (select(variantsTable)..where((t) => t.id.equals(variantId)))
          .getSingleOrNull();

  /// A standalone component product's qualified picker label, for example
  /// `RAM: 4 GB`. Returns null for ordinary products that are not referenced
  /// by an inventory-component option.
  Future<String?> componentDisplayNameForProduct(String productId) async {
    final productVariants = await variantsForProduct(productId);
    if (productVariants.isEmpty) return null;
    final option = await (select(variantOptionsTable)
          ..where((row) => row.componentVariantId
              .isIn(productVariants.map((variant) => variant.id))))
        .getSingleOrNull();
    if (option == null) return null;
    final group = await (select(variantOptionGroupsTable)
          ..where((row) => row.id.equals(option.optionGroupId)))
        .getSingleOrNull();
    if (group == null) return option.name;
    if (option.name.toLowerCase().contains(group.name.toLowerCase())) {
      return option.name;
    }
    return '${group.name}: ${option.name}';
  }

  Future<void> upsertVariants(List<VariantsTableCompanion> rows) =>
      batch((b) => b.insertAllOnConflictUpdate(variantsTable, rows));

  /// This device's branch stock row for [variantId], or null when untracked
  /// or not yet synced.
  Future<VariantBranchStockTableData?> branchStockForVariant(
          String variantId) =>
      (select(variantBranchStockTable)
            ..where((t) => t.variantId.equals(variantId)))
          .getSingleOrNull();

  Future<int> lowStockCount(String branchId, int threshold) async {
    final variants = await (select(variantsTable)
          ..where((v) =>
              v.tracksInventory.equals(true) &
              v.allowInventoryTracking.equals(true)))
        .get();
    final stockRows = await (select(variantBranchStockTable)
          ..where((s) => s.branchId.equals(branchId)))
        .get();
    final byVariant = {
      for (final row in stockRows) row.variantId: row.quantity
    };
    return variants
        .where((variant) => (byVariant[variant.id] ?? 0) <= threshold)
        .length;
  }

  Future<void> upsertVariantBranchStock(
          List<VariantBranchStockTableCompanion> rows) =>
      batch((b) => b.insertAllOnConflictUpdate(variantBranchStockTable, rows));

  /// Optimistic local write of one branch stock balance — used by
  /// [VariantInventory] to reserve/consume/roll back stock for offline and
  /// confirmed-online sales. The next sync always overwrites this with the
  /// server's authoritative figure.
  Future<void> setBranchStock(
          String variantId, String branchId, int quantity) =>
      into(variantBranchStockTable).insertOnConflictUpdate(
        VariantBranchStockTableCompanion.insert(
          variantId: variantId,
          branchId: branchId,
          quantity: Value(quantity),
        ),
      );

  // ── Add-on Groups + Items ──────────────────────────────────────

  /// Returns Add-on Groups for [productId], ordered by [displayOrder].
  ///
  /// Structurally separate from Variant Option Groups — never joined into
  /// variant resolution (spec A1/D4).
  Future<List<AddonGroupsTableData>> addonGroupsForProduct(String productId) =>
      (select(addonGroupsTable)
            ..where((t) => t.productId.equals(productId))
            ..orderBy([(t) => OrderingTerm.asc(t.displayOrder)]))
          .get();

  /// Returns active Add-on Items for [groupId], ordered by [displayOrder].
  Future<List<AddonItemsTableData>> addonItemsForGroup(String groupId) =>
      (select(addonItemsTable)
            ..where(
                (t) => t.addonGroupId.equals(groupId) & t.isActive.equals(true))
            ..orderBy([(t) => OrderingTerm.asc(t.displayOrder)]))
          .get();

  Future<void> upsertAddonGroups(List<AddonGroupsTableCompanion> rows) =>
      batch((b) => b.insertAllOnConflictUpdate(addonGroupsTable, rows));

  Future<void> upsertAddonItems(List<AddonItemsTableCompanion> rows) =>
      batch((b) => b.insertAllOnConflictUpdate(addonItemsTable, rows));

  // ── Deals ─────────────────────────────────────────────────────

  /// Returns all active deals (no ordering — UI handles display priority).
  Future<List<DealsTableData>> activeDeals() =>
      (select(dealsTable)..where((t) => t.isActive.equals(true))).get();

  /// Returns deal items for [dealId] ordered by [sortOrder] ascending.
  Future<List<DealItemsTableData>> itemsForDeal(String dealId) =>
      (select(dealItemsTable)
            ..where((t) => t.dealId.equals(dealId))
            ..orderBy([(t) => OrderingTerm.asc(t.sortOrder)]))
          .get();

  /// Upserts [rows] into the deals table; existing rows are fully replaced.
  Future<void> upsertDeals(List<DealsTableCompanion> rows) =>
      batch((b) => b.insertAllOnConflictUpdate(dealsTable, rows));

  /// Upserts [rows] into the deal_items table; existing rows are fully replaced.
  Future<void> upsertDealItems(List<DealItemsTableCompanion> rows) =>
      batch((b) => b.insertAllOnConflictUpdate(dealItemsTable, rows));

  // ── Promotions ────────────────────────────────────────────────

  /// Returns all active promotions (automatic and code-triggered).
  Future<List<PromotionsTableData>> activePromotions() =>
      (select(promotionsTable)..where((t) => t.isActive.equals(true))).get();

  /// Upserts [rows] into the promotions table; existing rows are fully replaced.
  Future<void> upsertPromotions(List<PromotionsTableCompanion> rows) =>
      batch((b) => b.insertAllOnConflictUpdate(promotionsTable, rows));

  // ── Stock (retired product-level path, kept for older local screens) ─────

  /// Current stock for every tracked product, keyed by productId. Cloud is
  /// authoritative — this is only ever overwritten by [upsertProductStock]
  /// (from a sync response) or nudged down optimistically by [decrementStock].
  Future<Map<String, String>> allStock() async {
    final rows = await select(localProductStockTable).get();
    return {for (final r in rows) r.productId: r.quantity};
  }

  /// Upserts [rows] into the local stock table; existing rows are fully replaced.
  Future<void> upsertProductStock(List<LocalProductStockTableCompanion> rows) =>
      batch((b) => b.insertAllOnConflictUpdate(localProductStockTable, rows));

  /// Optimistic local decrement so the order-picker doesn't oversell between
  /// syncs when a sale is queued offline. The next sync always overwrites
  /// this with the cloud's authoritative figure — see class doc.
  Future<void> decrementStock(String productId, double by) async {
    final row = await (select(localProductStockTable)
          ..where((t) => t.productId.equals(productId)))
        .getSingleOrNull();
    if (row == null) return; // untracked product — nothing to decrement
    final next = (double.tryParse(row.quantity) ?? 0) - by;
    await (update(localProductStockTable)
          ..where((t) => t.productId.equals(productId)))
        .write(
            LocalProductStockTableCompanion(quantity: Value(next.toString())));
  }
}
