import 'dart:convert';
import 'package:drift/drift.dart';

import '../../core/api/pos_sync_api.dart';
import '../../core/models/sync/pos_sync_response.dart';
import '../../core/models/sync/pos_upload_request.dart';
import '../../core/models/sync/pos_upload_response.dart';
import '../../db/app_database.dart';
import '../../db/daos/menu_dao.dart';
import '../../db/daos/tax_dao.dart';
import '../../db/daos/settings_dao.dart';

/// Orchestrates catalog synchronization between the cloud and the local DB.
///
/// Decides between full sync (first launch or forced) and delta sync (routine),
/// writes all received records via the appropriate DAOs, and updates the
/// `last_sync_at` cursor so the next delta only fetches what changed.
///
/// Data flows one way: cloud → tablet. This repository never sends catalog
/// data to the server.
class SyncRepository {
  final PosSyncApi _api;
  final AppDatabase _db;

  SyncRepository(this._api, this._db);

  MenuDao get _menu => _db.menuDao;
  TaxDao get _tax => _db.taxDao;
  SettingsDao get _settings => _db.settingsDao;

  /// Downloads the full catalog and replaces all local catalog tables.
  ///
  /// Called on first launch (no `last_sync_at`) or when a forced re-sync
  /// is triggered. Updates `last_sync_at` to the server's [PosSyncResponse.syncedAt].
  Future<void> fullSync() async {
    final res = await _api.fullSync();
    await _db.transaction(() async {
      if (await _settings.getBranchId() != res.branchId) {
        throw StateError(
            'Device activation changed while the catalog was downloading.');
      }
      if (await _db.syncDao.unsyncedCount() != 0) {
        throw StateError(
            'Upload pending sales before refreshing variant stock.');
      }
      if (res.inventoryModelVersion != 6) {
        throw StateError(
            'The server must support the Variant/Add-on catalog model before syncing this POS.');
      }
      await _db.clearCatalog();
      await _applyFull(res);
      await _settings.setCurrency(res.currency);
      await _settings.setLowStockThreshold(res.lowStockThreshold);
      await _settings.setPosLayout(res.posLayout);
      await _settings.saveReceiptProfile(
        businessName: res.businessName,
        branchName: res.branchName,
        branchCode: res.branchCode,
        branchAddress: res.branchAddress,
        branchPhone: res.branchPhone,
        logoBase64: res.receiptLogoBase64,
        tagline: res.receiptTagline,
        thankYou: res.receiptThankYou,
        terms: res.receiptTerms,
      );
      await _settings.setLastSyncAt(res.syncedAt);
    });
  }

  /// Downloads only records changed since `last_sync_at` and upserts them.
  ///
  /// Falls back to [fullSync] when no `last_sync_at` exists (first launch).
  /// Updates the cursor to [PosDeltaSyncResponse.syncedAt] on success.
  // A transactional full snapshot also propagates removals and option-only edits.
  Future<void> deltaSync() => fullSync();

  /// Forwards a batch of offline sales to the upload endpoint.
  ///
  /// Returns [PosUploadResponse] for the caller to inspect per-sale results
  /// and mark successfully uploaded sales as synced in the local DB.
  Future<PosUploadResponse> uploadOffline(PosUploadRequest req) =>
      _api.uploadOffline(req);

  /// Writes all catalog data from a full-sync response into the local DB.
  ///
  /// Uses upsert (insertOnConflictUpdate) throughout so re-running a full sync
  /// is safe — no duplicates are created. Variant Option Groups/Options and
  /// Add-on Groups/Items are two structurally separate trees (spec A1/D4),
  /// written to separate tables even though both are nested inside each
  /// product's sync payload.
  Future<void> _applyFull(PosSyncResponse r) async {
    await _menu.upsertCategories(r.categories
        .map((c) => CategoriesTableCompanion(
              id: Value(c.id),
              name: Value(c.name),
              description: Value(c.description),
              imagePath: Value(c.imagePath),
              displayOrder: Value(c.displayOrder),
              isActive: Value(c.isActive),
            ))
        .toList());

    await _menu.upsertProducts(r.products
        .map((p) => ProductsTableCompanion(
              id: Value(p.id),
              categoryId: Value(p.categoryId),
              productCode: Value(p.productCode),
              name: Value(p.name),
              description: Value(p.description),
              basePrice: Value(p.price),
              imagePath: Value(p.imagePath),
              displayOrder: Value(p.displayOrder),
              isActive: Value(p.isActive),
              trackInventory: const Value(false),
              allowNegativeStock: const Value(false),
            ))
        .toList());

    await _menu.upsertVariantOptionGroups(r.products
        .expand((p) => p.variantOptionGroups)
        .map((g) => VariantOptionGroupsTableCompanion(
              id: Value(g.id),
              productId: Value(g.productId),
              name: Value(g.name),
              isRequired: Value(g.isRequired),
              displayOrder: Value(g.displayOrder),
              usageType: Value(g.usageType),
              allowedOptionIds: Value(jsonEncode(g.allowedOptionIds)),
            ))
        .toList());

    await _menu.upsertVariantOptions(r.products
        .expand((p) => p.variantOptionGroups)
        .expand((g) => g.options)
        .map((o) => VariantOptionsTableCompanion(
              id: Value(o.id),
              optionGroupId: Value(o.optionGroupId),
              name: Value(o.name),
              displayOrder: Value(o.displayOrder),
              isActive: Value(o.isActive),
              componentVariantId: Value(o.componentVariantId),
            ))
        .toList());

    await _menu.upsertAddonGroups(r.products
        .expand((p) => p.addonGroups)
        .map((g) => AddonGroupsTableCompanion(
              id: Value(g.id),
              productId: Value(g.productId),
              name: Value(g.name),
              selectionType: Value(g.selectionType),
              minSelect: Value(g.minSelect),
              maxSelect: Value(g.maxSelect),
              displayOrder: Value(g.displayOrder),
            ))
        .toList());

    await _menu.upsertAddonItems(r.products
        .expand((p) => p.addonGroups)
        .expand((g) => g.items)
        .map((i) => AddonItemsTableCompanion(
              id: Value(i.id),
              addonGroupId: Value(i.addonGroupId),
              name: Value(i.name),
              priceDelta: Value(i.priceDelta),
              defaultSelected: Value(i.defaultSelected),
              displayOrder: Value(i.displayOrder),
              isActive: Value(i.isActive),
            ))
        .toList());

    await _menu.upsertVariants(r.variants
        .map((v) => VariantsTableCompanion(
              id: Value(v.id),
              productId: Value(v.productId),
              optionValueIds: Value(jsonEncode(v.optionValueIds)),
              salePrice: Value(v.salePrice),
              costPrice: Value(v.costPrice),
              comparePrice: Value(v.comparePrice),
              tracksInventory: Value(v.tracksInventory),
              isDefault: Value(v.isDefault),
              sellable: Value(v.sellable),
              sellableReason: Value(v.sellableReason),
              allowInventoryTracking: Value(v.allowInventoryTracking),
              productName: Value(v.productName),
              variantName: Value(v.variantName),
            ))
        .toList());

    // Only this device's own branch balance is ever synced (see
    // schemas.variant.SyncedVariantResponse.stock_by_branch on the server).
    await _menu.upsertVariantBranchStock(r.variants
        .where((v) => v.stockByBranch?.containsKey(r.branchId) ?? false)
        .map((v) => VariantBranchStockTableCompanion(
              variantId: Value(v.id),
              branchId: Value(r.branchId),
              quantity: Value(v.stockByBranch![r.branchId]!),
            ))
        .toList());

    await _tax.upsertRates(r.taxRates
        .map((t) => TaxRatesTableCompanion(
              id: Value(t.id),
              name: Value(t.name),
              rate: Value(t.rate),
              isInclusive: Value(t.isInclusive),
              isDefault: Value(t.isDefault),
            ))
        .toList());

    await _menu.upsertDeals(r.deals
        .map((d) => DealsTableCompanion(
              id: Value(d.id),
              name: Value(d.name),
              description: Value(d.description),
              dealCode: Value(d.dealCode),
              fixedPrice: Value(d.fixedPrice),
              discountValue: Value(d.discountValue),
              discountType: Value(d.discountType),
              validFrom: Value(d.validFrom),
              validUntil: Value(d.validUntil),
              isActive: Value(d.isActive),
            ))
        .toList());

    await _menu.upsertDealItems(r.deals
        .expand((d) => d.items.map((i) => (dealId: d.id, item: i)))
        .map((entry) => DealItemsTableCompanion(
              id: Value(entry.item.id),
              dealId: Value(entry.dealId),
              productId: Value(entry.item.productId),
              categoryId: Value(entry.item.categoryId),
              quantity: Value(entry.item.quantity),
              isFree: Value(entry.item.isFree),
              sortOrder: Value(entry.item.sortOrder),
            ))
        .toList());

    await _menu.upsertPromotions(r.promotions
        .map((p) => PromotionsTableCompanion(
              id: Value(p.id),
              name: Value(p.name),
              promoCode: Value(p.promoCode),
              type: Value(p.type),
              discountValue: Value(p.discountValue),
              triggerMinQty: Value(p.triggerMinQty),
              triggerMinAmount: Value(p.triggerMinAmount),
              triggerProductId: Value(p.triggerProductId),
              triggerCategoryId: Value(p.triggerCategoryId),
              validFrom: Value(p.validFrom),
              validUntil: Value(p.validUntil),
              maxUses: Value(p.maxUses),
              usedCount: Value(p.usedCount),
              isActive: Value(p.isActive),
            ))
        .toList());
  }
}
