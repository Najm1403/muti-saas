import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../core/api/pos_device_api.dart';
import '../core/models/sync/pos_offline_item.dart';
import '../core/models/sync/pos_offline_option.dart';
import '../core/models/sync/pos_offline_addon.dart';
import '../core/models/sync/pos_offline_payment.dart';
import '../core/models/sync/pos_offline_sale.dart';
import '../core/models/sync/pos_upload_request.dart';
import '../db/app_database.dart';
import '../features/sync/sync_repository.dart';
import '../providers/api_providers.dart';
import '../providers/auth_notifier.dart';
import '../providers/database_provider.dart';
import '../providers/onboarding_notifier.dart';
import '../providers/repository_providers.dart';

part 'sync_service.g.dart';

/// Background service that keeps the catalog up to date and drains the offline
/// sale outbox whenever connectivity is available.
///
/// Two jobs run concurrently:
///  - A `Timer.periodic` fires a delta sync every 5 minutes.
///  - A connectivity listener uploads pending sales and delta-syncs immediately
///    when the device comes back online after an outage.
class SyncService {
  final AppDatabase _db;
  final SyncRepository _syncRepo;
  final PosDeviceApi _deviceApi;

  Timer? _timer;
  StreamSubscription<List<ConnectivityResult>>? _connectivitySub;
  bool _wasOffline = false;
  bool _running = false;

  final void Function()? onSynced;
  SyncService(this._db, this._syncRepo, this._deviceApi, {this.onSynced});

  /// Starts the 5-minute periodic timer and connectivity listener.
  void start() {
    unawaited(_tick());
    _timer = Timer.periodic(const Duration(minutes: 5), (_) => _tick());

    _connectivitySub =
        Connectivity().onConnectivityChanged.listen((results) async {
      final isOnline = results.any((r) => r != ConnectivityResult.none);
      if (isOnline && _wasOffline) {
        // Came back online — drain outbox then refresh catalog.
        await _tick();
      }
      _wasOffline = !isOnline;
    });
  }

  /// Cancels all background jobs. Called by Riverpod's [onDispose].
  void dispose() {
    _timer?.cancel();
    _connectivitySub?.cancel();
  }

  Future<void> retryNow() => _tick();

  Future<void> _tick() async {
    if (_running) return;
    _running = true;
    try {
      final errors = <String>[];
      final uploadError = await _uploadPending();
      if (uploadError != null) errors.add(uploadError);
      final catalogError = await _deltaSync();
      if (catalogError != null) errors.add(catalogError);
      await _db.settingsDao.set('sync_error', errors.join('\n'));
      await _heartbeat();
    } finally {
      _running = false;
    }
  }

  /// Tells the server this device is alive, so the tenant dashboard's
  /// device/sync-health pages show an up-to-date `last_sync_at`. Silently
  /// swallowed like the other steps — offline or a server hiccup here must
  /// never block the catalog/sale sync that already ran this tick.
  Future<void> _heartbeat() async {
    try {
      await _deviceApi.heartbeat();
    } catch (_) {
      // Offline or server error — next tick retries.
    }
  }

  /// Uploads all unsynced, still-retryable local sales in a single batch
  /// request.
  ///
  /// Reads each sale's items, options, and payments from the DB, sends the
  /// batch, then marks sales reported as "created" or "duplicate" as synced.
  /// A sale the server rejects for a deterministic reason (see
  /// [PosUploadResult.retryable]) is quarantined via [SaleDao.markNeedsReview]
  /// instead of being resubmitted on every future tick — previously a single
  /// permanently-invalid sale would retry forever (every 5-minute tick and
  /// every reconnect), surfacing the identical error to the cashier
  /// indefinitely. Quarantined sales are still reported here on every tick
  /// (from local storage, no network call) so the sync banner doesn't go
  /// silent about a sale that genuinely needs an admin's attention.
  Future<String?> _uploadPending() async {
    try {
      final rawSales = await _db.saleDao.unsynced();
      if (rawSales.isEmpty) return await _reviewMessage();

      final sales = await Future.wait(rawSales.map(_buildOfflineSale));

      final response =
          await _syncRepo.uploadOffline(PosUploadRequest(sales: sales));

      final byNumber = {for (final sale in rawSales) sale.saleNumber: sale};

      // Match by saleNumber (the upload result key) back to local DB id.
      final syncedIds = rawSales
          .where((sale) => response.results.any((result) =>
              (result.status == 'created' || result.status == 'duplicate') &&
              result.saleId == sale.id &&
              result.saleNumber == sale.saleNumber))
          .map((sale) => sale.id)
          .toList();

      for (final result in response.results) {
        if (result.status != 'error' || result.retryable) continue;
        final sale = byNumber[result.saleNumber];
        if (sale != null) {
          await _db.saleDao
              .markNeedsReview(sale.id, result.error ?? 'Unknown error');
        }
      }

      final failures = response.results
          .where((result) => result.status == 'error' && result.retryable)
          .map((result) => '${result.saleNumber}: ${result.error}')
          .join('\n');
      if (syncedIds.isNotEmpty) {
        await _db.saleDao.markSynced(syncedIds);
      }

      final reviewMessage = await _reviewMessage();
      final messages = [
        if (failures.isNotEmpty) 'Sale upload failed:\n$failures',
        if (reviewMessage != null) reviewMessage,
      ];
      return messages.isEmpty ? null : messages.join('\n\n');
    } catch (error) {
      // Silently swallow — offline or server error; next tick retries.
      final reviewMessage = await _reviewMessage();
      final messages = [
        'Sale upload failed: $error',
        if (reviewMessage != null) reviewMessage,
      ];
      return messages.join('\n\n');
    }
  }

  Future<String?> _reviewMessage() async {
    final reviewSales = await _db.saleDao.needsReviewSales();
    if (reviewSales.isEmpty) return null;
    return 'Needs manual review (will not retry automatically):\n${reviewSales.map((s) => '${s.saleNumber}: ${s.syncError ?? 'Unknown error'}').join('\n')}';
  }

  Future<PosOfflineSale> _buildOfflineSale(LocalSalesTableData s) async {
    final items = await _db.saleDao.itemsForSale(s.id);
    final payments = await _db.saleDao.paymentsForSale(s.id);
    final offlineItems = await Future.wait(items.map(_buildOfflineItem));

    return PosOfflineSale(
      id: s.id,
      originProof: s.originProof,
      sessionId: s.sessionId,
      saleNumber: s.saleNumber,
      soldAt: s.soldAt,
      subtotal: s.subtotal,
      discount: s.discount,
      total: s.total,
      taxAmount: s.taxAmount,
      taxRate: s.taxRate,
      promotionId: s.promotionId,
      dealId: s.dealId,
      items: offlineItems,
      payments: payments
          .map((p) => PosOfflinePayment(
                paymentMethod: p.paymentMethod,
                amount: p.amount,
                reference: p.reference,
              ))
          .toList(),
    );
  }

  Future<PosOfflineItem> _buildOfflineItem(LocalSaleItemsTableData item) async {
    final opts = await _db.saleDao.optionsForItem(item.id);
    final addons = await _db.saleDao.addonsForItem(item.id);
    return PosOfflineItem(
      id: item.id,
      variantId: item.variantId ?? '',
      productId: item.productId,
      productName: item.productName,
      quantity: item.quantity,
      unitPrice: item.unitPrice,
      discount: item.discount,
      total: item.total,
      options: opts
          .map((o) => PosOfflineOption(
                variantOptionId: o.variantOptionId,
                optionName: o.optionName,
              ))
          .toList(),
      addons: addons
          .map((a) => PosOfflineAddon(
                addonItemId: a.addonItemId,
                addonName: a.addonName,
                priceDelta: a.priceDelta,
                wasRemoved: a.wasRemoved,
              ))
          .toList(),
      parentItemId: item.parentItemId,
      satisfiesOptionGroupId: item.satisfiesOptionGroupId,
      componentOptionId: item.componentOptionId,
    );
  }

  Future<String?> _deltaSync() async {
    try {
      await _syncRepo.deltaSync();
      onSynced?.call();
      return null;
    } catch (error) {
      return 'Catalog sync failed: $error';
      // Silently swallow — offline or server down is expected.
    }
  }
}

/// Singleton [SyncService] provider.
///
/// Watching this provider (once, in [main.dart]) starts the background jobs
/// for the lifetime of the app. [onDispose] cancels the timer and stream
/// subscription if the [ProviderScope] is ever torn down.
@Riverpod(keepAlive: true)
SyncService syncService(SyncServiceRef ref) {
  final service = SyncService(
    ref.watch(appDatabaseProvider),
    ref.watch(syncRepositoryProvider),
    ref.watch(posDeviceApiProvider),
    onSynced: () => ref.invalidate(menuRepositoryProvider),
  );
  service.start();
  ref.listen(onboardingNotifierProvider, (previous, next) {
    final wasOnboarded = previous?.valueOrNull?.onboarded ?? false;
    final isOnboarded = next.valueOrNull?.onboarded ?? false;
    if (!wasOnboarded && isOnboarded) unawaited(service.retryNow());
  });
  ref.listen(authNotifierProvider, (previous, next) {
    final wasLoggedIn = previous?.valueOrNull?.isCashierLoggedIn ?? false;
    final isLoggedIn = next.valueOrNull?.isCashierLoggedIn ?? false;
    if (!wasLoggedIn && isLoggedIn) unawaited(service.retryNow());
  });
  ref.onDispose(service.dispose);
  return service;
}
