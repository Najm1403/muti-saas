import '../../db/app_database.dart';
import '../../db/daos/menu_dao.dart';
import '../../db/daos/settings_dao.dart';
import '../../db/daos/tax_dao.dart';

/// Read-only facade over the local catalog tables for use by UI layers.
///
/// Delegates to [MenuDao] and [TaxDao] so feature code never imports
/// Drift directly. All methods return data from the local SQLite DB —
/// network sync is handled separately by [SyncRepository].
class MenuRepository {
  final AppDatabase _db;

  MenuRepository(this._db);

  MenuDao get _menu => _db.menuDao;
  TaxDao get _tax => _db.taxDao;
  SettingsDao get _settings => _db.settingsDao;

  /// The tenant's Business-Template-driven POS layout (spec Part C / F3/G4),
  /// synced from the cloud and cached so it works offline. Invalidated by
  /// the same `ref.invalidate(menuRepositoryProvider)` call every other
  /// synced value uses after a sync completes.
  Future<String> posLayout() => _settings.getPosLayout();

  Future<int> lowStockThreshold() => _settings.getLowStockThreshold();

  Future<int> lowStockCount() async {
    final branchId = await _settings.getBranchId();
    if (branchId == null) return 0;
    return _menu.lowStockCount(branchId, await lowStockThreshold());
  }

  /// Returns all categories ordered by display_order.
  Future<List<CategoriesTableData>> categories() => _menu.allCategories();

  /// Returns active products in [categoryId] ordered by display_order.
  Future<List<ProductsTableData>> productsByCategory(String categoryId) =>
      _menu.productsByCategory(categoryId);

  /// Returns all active products across all categories.
  Future<List<ProductsTableData>> allActiveProducts() => _menu.activeProducts();

  /// Returns active products matching [query] by name, product code, or an
  /// attached Variant Selection group/option name. Empty query → empty list.
  Future<List<ProductsTableData>> searchProducts(String query) =>
      _menu.searchProducts(query);

  /// Returns Variant Option Groups for [productId] ordered by display_order.
  Future<List<VariantOptionGroupsTableData>> variantOptionGroupsForProduct(
          String productId) =>
      _menu.variantOptionGroupsForProduct(productId);

  /// Returns active Variant Options for [groupId] ordered by display_order.
  Future<List<VariantOptionsTableData>> variantOptionsForGroup(
          String groupId) =>
      _menu.variantOptionsForGroup(groupId);

  /// Returns every synced composed Variant for [productId].
  Future<List<VariantsTableData>> variantsForProduct(String productId) =>
      _menu.variantsForProduct(productId);

  /// Returns the single Variant row with [variantId], or null.
  Future<VariantsTableData?> variantById(String variantId) =>
      _menu.variantById(variantId);

  /// Qualified name for products used as shared inventory components.
  Future<String?> componentDisplayNameForProduct(String productId) =>
      _menu.componentDisplayNameForProduct(productId);

  /// This device's branch stock row for [variantId], or null.
  Future<VariantBranchStockTableData?> branchStockForVariant(
          String variantId) =>
      _menu.branchStockForVariant(variantId);

  /// Returns Add-on Groups for [productId] ordered by display_order.
  Future<List<AddonGroupsTableData>> addonGroupsForProduct(String productId) =>
      _menu.addonGroupsForProduct(productId);

  /// Returns active Add-on Items for [groupId] ordered by display_order.
  Future<List<AddonItemsTableData>> addonItemsForGroup(String groupId) =>
      _menu.addonItemsForGroup(groupId);

  /// Returns all tax rates configured for this branch.
  Future<List<TaxRatesTableData>> taxRates() => _tax.allRates();

  /// Returns the default tax rate, or null if none is marked default.
  Future<TaxRatesTableData?> defaultTaxRate() => _tax.defaultRate();

  /// Returns all currently active deals.
  Future<List<DealsTableData>> activeDeals() => _menu.activeDeals();

  /// Returns the component items of [dealId] ordered by sort_order.
  Future<List<DealItemsTableData>> dealItems(String dealId) =>
      _menu.itemsForDeal(dealId);

  /// Returns all currently active promotions (automatic and code-triggered).
  Future<List<PromotionsTableData>> activePromotions() =>
      _menu.activePromotions();

  /// Current stock for every tracked product, keyed by productId (String —
  /// Decimal, see LocalProductStockTable). A product with no entry here is
  /// either untracked or has never synced a stock figure.
  Future<Map<String, String>> productStock() => _menu.allStock();
}
