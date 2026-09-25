import 'dart:io';
import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

import 'tables/categories_table.dart';
import 'tables/products_table.dart';
import 'tables/variant_option_groups_table.dart';
import 'tables/variant_options_table.dart';
import 'tables/variants_table.dart';
import 'tables/variant_branch_stock_table.dart';
import 'tables/addon_groups_table.dart';
import 'tables/addon_items_table.dart';
import 'tables/tax_rates_table.dart';
import 'tables/deals_table.dart';
import 'tables/deal_items_table.dart';
import 'tables/promotions_table.dart';
import 'tables/local_sales_table.dart';
import 'tables/local_sale_items_table.dart';
import 'tables/local_sale_item_options_table.dart';
import 'tables/local_sale_item_addons_table.dart';
import 'tables/local_payments_table.dart';
import 'tables/local_product_stock_table.dart';
import 'tables/app_settings_table.dart';
import 'daos/menu_dao.dart';
import 'daos/tax_dao.dart';
import 'daos/sale_dao.dart';
import 'daos/sync_dao.dart';
import 'daos/settings_dao.dart';

part 'app_database.g.dart';

/// Root Drift database for the POS tablet app.
///
/// Contains all local tables split across two groups:
/// - Catalog tables ([CategoriesTable], [ProductsTable], [VariantsTable] etc.)
///   — populated by sync and never written to by sale or session logic.
/// - Transactional tables ([LocalSalesTable] and children) — a bounded local
///   report cache plus the durable, never-auto-deleted unsynced outbox.
///
/// DAOs are used exclusively for all queries; direct table access from outside
/// this file is avoided to keep SQL logic centralized.
@DriftDatabase(
  tables: [
    CategoriesTable,
    ProductsTable,
    VariantOptionGroupsTable,
    VariantOptionsTable,
    VariantsTable,
    VariantBranchStockTable,
    AddonGroupsTable,
    AddonItemsTable,
    TaxRatesTable,
    DealsTable,
    DealItemsTable,
    PromotionsTable,
    LocalSalesTable,
    LocalSaleItemsTable,
    LocalSaleItemOptionsTable,
    LocalSaleItemAddonsTable,
    LocalPaymentsTable,
    LocalProductStockTable,
    AppSettingsTable,
  ],
  daos: [
    MenuDao,
    TaxDao,
    SaleDao,
    SyncDao,
    SettingsDao,
  ],
)
class AppDatabase extends _$AppDatabase {
  AppDatabase() : super(_openConnection());
  AppDatabase.forTesting(super.e);

  Future<void> clearCatalog() async {
    for (final table in <TableInfo>[
      addonItemsTable,
      addonGroupsTable,
      variantBranchStockTable,
      variantsTable,
      variantOptionsTable,
      variantOptionGroupsTable,
      dealItemsTable,
      dealsTable,
      promotionsTable,
      localProductStockTable,
      productsTable,
      categoriesTable,
      taxRatesTable,
    ]) {
      await delete(table).go();
    }
  }

  Future<void> clearDeviceData() async {
    await transaction(() async {
      if (await syncDao.unsyncedCount() != 0) {
        throw StateError(
            'Sync pending sales before changing device activation.');
      }
      await clearCatalog();
      for (final table in <TableInfo>[
        localSaleItemAddonsTable,
        localSaleItemOptionsTable,
        localSaleItemsTable,
        localPaymentsTable,
        localSalesTable,
        appSettingsTable,
      ]) {
        await delete(table).go();
      }
    });
  }

  @override
  int get schemaVersion => 14;

  @override
  MigrationStrategy get migration => MigrationStrategy(
        /// On first install, create all tables from their Drift definitions.
        onCreate: (m) => m.createAll(),
        onUpgrade: (m, from, to) async {
          if (from < 3) {
            await m.addColumn(localSalesTable, localSalesTable.originProof);
            await m.addColumn(localSalesTable, localSalesTable.sessionId);
          }
          if (from < 7) {
            await m.addColumn(
                localSaleItemsTable, localSaleItemsTable.variantId);
          }
          if (from < 2) {
            // Inventory: product-level flags + the new branch stock table.
            await m.addColumn(productsTable, productsTable.trackInventory);
            await m.addColumn(productsTable, productsTable.allowNegativeStock);
            await m.createTable(localProductStockTable);
          }
          if (from < 8) {
            // Structural split (Variant vs Add-on, spec A1) replaces the old
            // flat option_groups/options tables and the JSON-blob variant
            // inventory shim with real queryable tables. All of this is
            // synced catalog data — safe to drop and let the next sync refill.
            await customStatement('DROP TABLE IF EXISTS option_groups');
            await customStatement('DROP TABLE IF EXISTS options');
            await customStatement(
                'DROP TABLE IF EXISTS local_variant_stock_table');
            await m.createTable(variantOptionGroupsTable);
            await m.createTable(variantOptionsTable);
            await m.createTable(variantsTable);
            await m.createTable(variantBranchStockTable);
            await m.createTable(addonGroupsTable);
            await m.createTable(addonItemsTable);
            await m.createTable(localSaleItemAddonsTable);
          }
          if (from < 9) {
            // Real "why" for an unsellable variant (e.g. a Variant Option
            // Group attached after the SKU was created), instead of always
            // guessing at a generic message client-side.
            await m.addColumn(variantsTable, variantsTable.sellableReason);
          }
          if (from < 10) {
            // Laptop Store shareable-inventory model — a Component Group's
            // usage_type/allowed_option_ids, an option's own resolved
            // component Variant, and the component-selection pairing tags
            // on an offline-queued sale line (see cart_service.dart's
            // CartItem — a selected component is an ordinary row here, not
            // a nested child, so pricing/stock code needs no new branch).
            await m.addColumn(
                variantOptionGroupsTable, variantOptionGroupsTable.usageType);
            await m.addColumn(variantOptionGroupsTable,
                variantOptionGroupsTable.allowedOptionIds);
            await m.addColumn(
                variantOptionsTable, variantOptionsTable.componentVariantId);
            await m.addColumn(
                localSaleItemsTable, localSaleItemsTable.parentItemId);
            await m.addColumn(localSaleItemsTable,
                localSaleItemsTable.satisfiesOptionGroupId);
            await m.addColumn(
                localSaleItemsTable, localSaleItemsTable.componentOptionId);
          }
          if (from < 11) {
            // Serial tracking retired — every Variant is quantity-tracked now.
            await customStatement('DROP TABLE IF EXISTS variant_serials');
            if (from >= 8) {
              await customStatement(
                  'ALTER TABLE variants DROP COLUMN tracking_mode');
              await customStatement(
                  'ALTER TABLE local_sale_items DROP COLUMN serial_numbers');
            }
          }
          if (from < 12) {
            // Cashier name was never captured for offline-queued sales, so
            // the receipt/recent-sales screens showed it blank until sync.
            await m.addColumn(localSalesTable, localSalesTable.cashierName);
          }
          if (from < 13) {
            // Keep enough authoritative sale metadata for useful offline
            // reports grouped by cashier and shift.
            await m.addColumn(localSalesTable, localSalesTable.cashierId);
            await m.addColumn(localSalesTable, localSalesTable.status);
          }
          if (from < 14) {
            // A sale the server rejects for a deterministic reason (bad
            // data, a genuine conflict) used to retry forever — every
            // 5-minute sync tick and every reconnect resubmitted it and hit
            // the identical error again. These columns let SyncService
            // quarantine it after the first such rejection instead.
            await m.addColumn(localSalesTable, localSalesTable.needsReview);
            await m.addColumn(localSalesTable, localSalesTable.syncError);
          }
        },
      );
}

/// Opens (or lazily creates) the SQLite file in the app's documents directory.
///
/// [NativeDatabase.createInBackground] runs the initial open on a background
/// isolate so the UI is not blocked on first launch when the file is created.
LazyDatabase _openConnection() {
  return LazyDatabase(() async {
    final dir = await getApplicationDocumentsDirectory();
    final file = File(p.join(dir.path, 'pos.db'));
    return NativeDatabase.createInBackground(file);
  });
}
