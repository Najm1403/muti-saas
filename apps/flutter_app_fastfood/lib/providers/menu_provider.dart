import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../db/app_database.dart';
import 'repository_providers.dart';

part 'menu_provider.g.dart';

final lowStockThresholdProvider = FutureProvider<int>(
    (ref) => ref.watch(menuRepositoryProvider).lowStockThreshold());

final lowStockCountProvider = FutureProvider.autoDispose<int>(
    (ref) => ref.watch(menuRepositoryProvider).lowStockCount());

/// All categories from the local catalog, ordered by display_order.
///
/// Refetch by invalidating this provider after a sync completes.
@riverpod
Future<List<CategoriesTableData>> categories(CategoriesRef ref) =>
    ref.watch(menuRepositoryProvider).categories();

/// Active products in [categoryId], ordered by display_order.
///
/// The family key is the category UUID. Invalidate the whole family after sync.
@riverpod
Future<List<ProductsTableData>> productsByCategory(
  ProductsByCategoryRef ref,
  String categoryId,
) =>
    ref.watch(menuRepositoryProvider).productsByCategory(categoryId);

/// Active products across every category.
///
/// Used for search/lookup screens where a flat product list is needed.
@riverpod
Future<List<ProductsTableData>> allActiveProducts(AllActiveProductsRef ref) =>
    ref.watch(menuRepositoryProvider).allActiveProducts();

/// Active products matching a free-text [query] (name / product code /
/// attached Variant Selection group or option name), spanning every
/// category. The family key is the trimmed, lower-cased search text.
@riverpod
Future<List<ProductsTableData>> searchProducts(
  SearchProductsRef ref,
  String query,
) =>
    ref.watch(menuRepositoryProvider).searchProducts(query);

/// A standalone inventory component's qualified picker name (`RAM: 4 GB`).
@riverpod
Future<String?> componentDisplayName(
  ComponentDisplayNameRef ref,
  String productId,
) =>
    ref.watch(menuRepositoryProvider).componentDisplayNameForProduct(productId);

/// Variant Option Groups attached to [productId], ordered by display_order.
///
/// Structurally separate from [addonGroupsProvider] — never feeds into
/// variant generation (spec A1/D4).
@riverpod
Future<List<VariantOptionGroupsTableData>> variantOptionGroups(
  VariantOptionGroupsRef ref,
  String productId,
) =>
    ref.watch(menuRepositoryProvider).variantOptionGroupsForProduct(productId);

/// Active Variant Options inside [groupId], ordered by display_order.
@riverpod
Future<List<VariantOptionsTableData>> variantOptionsForGroup(
  VariantOptionsForGroupRef ref,
  String groupId,
) =>
    ref.watch(menuRepositoryProvider).variantOptionsForGroup(groupId);

/// Every synced composed Variant for [productId] — the real, sellable SKUs.
///
/// A product with no attached Variant Option Groups still has exactly one
/// (the zero-option default) row here.
@riverpod
Future<List<VariantsTableData>> variantsForProduct(
  VariantsForProductRef ref,
  String productId,
) =>
    ref.watch(menuRepositoryProvider).variantsForProduct(productId);

/// The single Variant row for [variantId] — used to price/resolve a
/// selected Inventory Component (Laptop Store shareable-inventory model),
/// which belongs to a different product than the one currently open in the
/// picker, so it isn't already present in [variantsForProduct].
@riverpod
Future<VariantsTableData?> variantById(VariantByIdRef ref, String variantId) =>
    ref.watch(menuRepositoryProvider).variantById(variantId);

/// This device's branch stock row for [variantId], or null when untracked.
@riverpod
Future<VariantBranchStockTableData?> branchStockForVariant(
  BranchStockForVariantRef ref,
  String variantId,
) =>
    ref.watch(menuRepositoryProvider).branchStockForVariant(variantId);

/// Add-on Groups attached to [productId], ordered by display_order.
@riverpod
Future<List<AddonGroupsTableData>> addonGroups(
  AddonGroupsRef ref,
  String productId,
) =>
    ref.watch(menuRepositoryProvider).addonGroupsForProduct(productId);

/// Active Add-on Items inside [groupId], ordered by display_order.
@riverpod
Future<List<AddonItemsTableData>> addonItemsForGroup(
  AddonItemsForGroupRef ref,
  String groupId,
) =>
    ref.watch(menuRepositoryProvider).addonItemsForGroup(groupId);

/// The default tax rate for this branch, or null when none is configured.
///
/// Used during cart construction to pre-fill the tax rate for new sales.
@riverpod
Future<TaxRatesTableData?> defaultTaxRate(DefaultTaxRateRef ref) =>
    ref.watch(menuRepositoryProvider).defaultTaxRate();

/// All currently active deals available for the cashier to apply.
@riverpod
Future<List<DealsTableData>> activeDeals(ActiveDealsRef ref) =>
    ref.watch(menuRepositoryProvider).activeDeals();

/// The product/category slots belonging to [dealId], ordered by sort_order.
@riverpod
Future<List<DealItemsTableData>> dealItemsForDeal(
  DealItemsForDealRef ref,
  String dealId,
) =>
    ref.watch(menuRepositoryProvider).dealItems(dealId);

/// Active promotions (both automatic and code-triggered).
@riverpod
Future<List<PromotionsTableData>> activePromotions(ActivePromotionsRef ref) =>
    ref.watch(menuRepositoryProvider).activePromotions();

/// Retired product stock map kept for compatibility with older local screens.
/// Active inventory enforcement uses real Variant/VariantBranchStock queries.
@riverpod
Future<Map<String, String>> productStock(ProductStockRef ref) =>
    ref.watch(menuRepositoryProvider).productStock();

/// The tenant's Business-Template-driven POS layout (spec Part C / F3/G4) —
/// `'grid_with_variant_picker'` or `'grid_quick_tap'`. Synced from the cloud,
/// cached locally so the POS picks its layout even offline. Defaults to the
/// side-panel layout when unset.
@riverpod
Future<String> posLayout(PosLayoutRef ref) =>
    ref.watch(menuRepositoryProvider).posLayout();
