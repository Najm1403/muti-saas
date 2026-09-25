import 'package:decimal/decimal.dart';
import 'variant_inventory.dart';
import '../../core/security/token_storage.dart';
import 'package:drift/drift.dart';
import 'package:uuid/uuid.dart';

import '../../core/api/pos_sale_api.dart';
import '../../core/models/sale/pos_sale_create.dart';
import '../../core/models/sale/pos_receipt_item.dart';
import '../../core/models/sale/pos_receipt_payment.dart';
import '../../core/models/sale/pos_receipt_response.dart';
import '../../core/network/api_exception.dart';
import '../../db/app_database.dart';
import '../../db/daos/sale_dao.dart';
import 'cart_service.dart';

/// Bridges [CartService] to the cloud API (online path) or local DB (offline path).
///
/// On every sale submission:
///   1. A UUID and sale number are generated deterministically.
///   2. If online, the sale is sent to the API; on success the local copy
///      (if any) is marked synced.
///   3. If offline (or the API returns [ApiException.isOffline]), the sale is
///      written to the local DB queue for later batch upload.
///
/// Callers inspect the returned [SaleResult] to determine which path was taken
/// and, in the online case, access the server receipt.
class SaleRepository {
  final PosSaleApi _api;
  final AppDatabase _db;

  final TokenStorage _tokens;
  SaleRepository(this._api, this._db, this._tokens);

  SaleDao get _sales => _db.saleDao;

  /// Submits the [cart] snapshot as a sale.
  ///
  /// When [isOnline] is true the API is attempted first; a connectivity
  /// [ApiException] transparently falls back to the offline queue.
  /// Non-connectivity API errors (e.g. 400 validation) are re-thrown.
  /// Returns [SaleResult.online] with the receipt on success, or
  /// [SaleResult.queued] when the sale is stored locally for later upload.
  Future<SaleResult> submitSale(
    CartSnapshot cart, {
    required bool isOnline,
    String? cashierName,
    String? cashierId,
    String? sessionId,
  }) async {
    // A manual discount (cashier-entered, not from a Promotion/Deal) needs
    // its eligibility re-verified against the server's current
    // sales.discount permission — same discriminator as the backend
    // (services/offer_service.py::OfferService.validate): a discount with
    // neither promotionId nor dealId set is "manual". An offline-queued
    // sale can't have that re-verified until it syncs, so it must go online.
    final isManualDiscount = cart.discount > Decimal.zero &&
        cart.promotionId == null &&
        cart.dealId == null;
    if (isManualDiscount && !isOnline) {
      throw StateError(
          'A manual discount requires an online permission check.');
    }
    final id = const Uuid().v4();
    final now = DateTime.now();
    final branchCode = ((await _db.settingsDao.getBranchCode()) ?? 'POS')
        .toUpperCase()
        .replaceAll(RegExp(r'[^A-Z0-9]'), '');
    // Folded into the number so two devices at the same branch — which
    // otherwise share an identical branchCode and each keep their own
    // independent local counter starting at 0 — can never generate the same
    // sale_number (see settingsDao.nextSaleCounter()'s doc comment).
    final deviceLetter = ((await _db.settingsDao.getDeviceLetter()) ?? '')
        .toUpperCase()
        .replaceAll(RegExp(r'[^A-Z0-9]'), '');
    final sequence = await _db.settingsDao.nextSaleCounter();
    final saleNumber = [
      branchCode,
      if (deviceLetter.isNotEmpty) deviceLetter,
      (now.year % 100).toString().padLeft(2, '0'),
      sequence.toString().padLeft(6, '0'),
    ].join('-');

    final create = cart.toPosSaleCreate(
      id: id,
      saleNumber: saleNumber,
      sessionId: sessionId,
    );

    if (isOnline) {
      try {
        final receipt = await _withLocalBranding(await _api.createSale(create));
        // Retain confirmed online sales in SQLite as well. Reporting must
        // continue to work during a later network outage.
        await _persistLocal(
          id,
          saleNumber,
          cart,
          create,
          cashierName,
          cashierId,
          sessionId,
          synced: true,
          reserveStock: false,
        );
        await VariantInventory(_db).consumeConfirmed(cart);
        await _sales.pruneSyncedOlderThan(
          DateTime.now().toUtc().subtract(const Duration(days: 90)),
        );
        return SaleResult.online(receipt);
      } on ApiException catch (e) {
        if (e.isOffline && !isManualDiscount) {
          // Network unreachable — queue locally and report as queued.
          await _persistLocal(
              id, saleNumber, cart, create, cashierName, cashierId, sessionId,
              synced: false, reserveStock: true);
          return const SaleResult.queued();
        }
        rethrow;
      }
    } else {
      await _persistLocal(
          id, saleNumber, cart, create, cashierName, cashierId, sessionId,
          synced: false, reserveStock: true);
      return const SaleResult.queued();
    }
  }

  /// Fetches the server receipt for an already-submitted sale by [saleId].
  Future<PosReceiptResponse> getReceipt(String saleId) async =>
      _withLocalBranding(await _api.getReceipt(saleId));

  /// Uses the locally synced profile as a durable fallback. This keeps
  /// reprints branded even when an older server response omits optional data.
  Future<PosReceiptResponse> _withLocalBranding(
      PosReceiptResponse receipt) async {
    final settings = _db.settingsDao;
    String prefer(String current, String? local) =>
        current.isNotEmpty ? current : (local ?? '');
    String? preferOptional(String? current, String? local) =>
        current?.isNotEmpty == true ? current : local;
    return PosReceiptResponse(
      saleId: receipt.saleId,
      sessionId: receipt.sessionId,
      userId: receipt.userId,
      saleNumber: receipt.saleNumber,
      status: receipt.status,
      soldAt: receipt.soldAt,
      branchName: prefer(receipt.branchName, await settings.getBranchName()),
      branchCode: prefer(receipt.branchCode, await settings.getBranchCode()),
      branchAddress: preferOptional(
          receipt.branchAddress, await settings.getBranchAddress()),
      branchPhone:
          preferOptional(receipt.branchPhone, await settings.getBranchPhone()),
      businessName:
          prefer(receipt.businessName, await settings.getBusinessName()),
      currency: receipt.currency.isNotEmpty
          ? receipt.currency
          : await settings.getCurrency(),
      receiptLogoBase64: preferOptional(
          receipt.receiptLogoBase64, await settings.getReceiptLogoBase64()),
      receiptTagline: preferOptional(
          receipt.receiptTagline, await settings.getReceiptTagline()),
      receiptThankYou: preferOptional(
          receipt.receiptThankYou, await settings.getReceiptThankYou()),
      receiptTerms: preferOptional(
          receipt.receiptTerms, await settings.getReceiptTerms()),
      cashierName: receipt.cashierName,
      items: receipt.items,
      subtotal: receipt.subtotal,
      discount: receipt.discount,
      taxAmount: receipt.taxAmount,
      taxRate: receipt.taxRate,
      total: receipt.total,
      payments: receipt.payments,
      change: receipt.change,
    );
  }

  Future<PosReceiptResponse> getReceiptByNumber(String saleNumber) async =>
      _withLocalBranding(await _api.getReceiptByNumber(saleNumber));

  Future<List<PosReceiptResponse>> recentSales({
    int limit = 200,
    DateTime? dateFrom,
    DateTime? dateTo,
    String? sessionId,
    String? cashierId,
  }) async {
    final localRows = await _sales.recentSales(
      dateFrom: dateFrom,
      dateTo: dateTo,
      sessionId: sessionId,
      cashierId: cashierId,
    );
    final localReceipts =
        await Future.wait(localRows.take(limit).map(_localReceipt));

    List<PosReceiptResponse> remoteReceipts;
    try {
      remoteReceipts = await _api.recentSales(
        // The cloud receipt endpoint intentionally caps its heavier nested
        // response at 200. SQLite may retain more rows for offline reports.
        limit: limit.clamp(1, 200),
        dateFrom: dateFrom,
        dateTo: dateTo,
        sessionId: sessionId,
      );
      if (cashierId != null) {
        remoteReceipts = remoteReceipts
            .where((receipt) => receipt.userId == cashierId)
            .toList();
      }
    } on ApiException catch (error) {
      if (!error.isOffline) rethrow;
      remoteReceipts = const [];
    }

    // A sale can exist in both stores after offline upload. Prefer the server
    // receipt because it contains the authoritative status and return data.
    final merged = <String, PosReceiptResponse>{
      for (final receipt in localReceipts) receipt.saleNumber: receipt,
      for (final receipt in remoteReceipts)
        receipt.saleNumber: await _withLocalBranding(receipt),
    };
    final result = merged.values.toList()
      ..sort((a, b) => b.soldAt.compareTo(a.soldAt));
    return result.take(limit).toList();
  }

  Future<PosReceiptResponse> _localReceipt(LocalSalesTableData sale) async {
    final items = await _sales.itemsForSale(sale.id);
    final payments = await _sales.paymentsForSale(sale.id);
    final settings = _db.settingsDao;
    return PosReceiptResponse(
      saleId: sale.id,
      sessionId: sale.sessionId,
      userId: sale.cashierId,
      saleNumber: sale.saleNumber,
      status: sale.synced ? sale.status : 'QUEUED',
      soldAt: sale.soldAt,
      branchName: await settings.getBranchName() ?? '',
      branchCode: await settings.getBranchCode() ?? '',
      branchAddress: await settings.getBranchAddress(),
      branchPhone: await settings.getBranchPhone(),
      businessName: await settings.getBusinessName() ?? '',
      currency: await settings.getCurrency(),
      receiptLogoBase64: await settings.getReceiptLogoBase64(),
      receiptTagline: await settings.getReceiptTagline(),
      receiptThankYou: await settings.getReceiptThankYou(),
      receiptTerms: await settings.getReceiptTerms(),
      cashierName: sale.cashierName ?? '',
      items: items
          .map((item) => PosReceiptItem(
                id: item.id,
                parentItemId: item.parentItemId,
                productName: item.productName,
                quantity: item.quantity,
                unitPrice: item.unitPrice,
                discount: item.discount,
                total: item.total,
              ))
          .toList(),
      subtotal: sale.subtotal,
      discount: sale.discount,
      taxAmount: sale.taxAmount,
      taxRate: sale.taxRate,
      total: sale.total,
      payments: payments
          .map((payment) => PosReceiptPayment(
                paymentMethod: payment.paymentMethod,
                amount: payment.amount,
                reference: payment.reference,
              ))
          .toList(),
      change: '0.00',
    );
  }

  Future<Map<String, dynamic>> cancelSale(String saleId, String reason) async {
    final result = await _api.cancelSale(saleId, reason);
    await _sales.updateStatus(saleId, 'CANCELLED');
    return result;
  }

  /// A return may be partial (sale stays COMPLETED) or, once every item has
  /// been returned, full (sale becomes REFUNDED) — the return response
  /// itself doesn't say which, so the receipt is re-fetched to learn the
  /// authoritative status and keep the local cache from showing a fully
  /// refunded sale as still COMPLETED. Best-effort: the return itself has
  /// already succeeded even if this follow-up refresh fails offline.
  Future<Map<String, dynamic>> returnItems(
      String saleId, List<Map<String, dynamic>> items, String? reason) async {
    final result = await _api.returnItems(saleId, items, reason);
    try {
      final receipt = await _api.getReceipt(saleId);
      await _sales.updateStatus(saleId, receipt.status);
    } catch (_) {
      // Server is the source of truth; local status just stays stale
      // until the next successful recentSales() merge.
    }
    return result;
  }

  /// Returns all local sales that have not yet been uploaded to the server.
  Future<List<LocalSalesTableData>> unsyncedSales() => _sales.unsynced();

  /// Persists the sale and all its children to the local offline queue.
  Future<void> _persistLocal(
    String id,
    String saleNumber,
    CartSnapshot cart,
    PosSaleCreate create,
    String? cashierName,
    String? cashierId,
    String? sessionId, {
    required bool synced,
    required bool reserveStock,
  }) async {
    if (!synced && _tokens.offlineProof == null) {
      throw StateError('Sign in again before recording offline sales.');
    }
    final saleCompanion = LocalSalesTableCompanion(
      id: Value(id),
      saleNumber: Value(saleNumber),
      originProof: Value(_tokens.offlineProof),
      sessionId: Value(sessionId),
      cashierId: Value(cashierId),
      cashierName: Value(cashierName),
      status: const Value('COMPLETED'),
      soldAt: Value(create.soldAt),
      subtotal: Value(create.subtotal),
      discount: Value(create.discount),
      total: Value(create.total),
      taxAmount: Value(create.taxAmount),
      taxRate: Value(create.taxRate),
      promotionId: Value(create.promotionId),
      dealId: Value(create.dealId),
      synced: Value(synced),
    );

    final itemCompanions = create.items
        .map((i) => LocalSaleItemsTableCompanion(
              id: Value(i.id ?? const Uuid().v4()),
              saleId: Value(id),
              variantId: Value(i.variantId),
              productId: Value(i.productId),
              productName: Value(i.productName),
              quantity: Value(i.quantity),
              unitPrice: Value(i.unitPrice),
              discount: Value(i.discount),
              total: Value(i.total),
              parentItemId: Value(i.parentItemId),
              satisfiesOptionGroupId: Value(i.satisfiesOptionGroupId),
              componentOptionId: Value(i.componentOptionId),
            ))
        .toList();

    final itemOptions = create.items.map((i) {
      final itemId = i.id ?? '';
      return (
        itemId: itemId,
        opts: i.options
            .map((o) => LocalSaleItemOptionsTableCompanion(
                  id: Value(o.id ?? const Uuid().v4()),
                  saleItemId: Value(itemId),
                  variantOptionId: Value(o.variantOptionId),
                  optionName: Value(o.optionName),
                  priceAdjustment: const Value('0.00'),
                ))
            .toList(),
        addons: i.addons
            .map((a) => LocalSaleItemAddonsTableCompanion(
                  id: Value(a.id ?? const Uuid().v4()),
                  saleItemId: Value(itemId),
                  addonItemId: Value(a.addonItemId),
                  addonName: Value(a.addonName),
                  priceDelta: Value(a.priceDelta),
                  wasRemoved: Value(a.wasRemoved),
                ))
            .toList(),
      );
    }).toList();

    final paymentCompanions = create.payments
        .map((p) => LocalPaymentsTableCompanion(
              id: Value(const Uuid().v4()),
              saleId: Value(id),
              paymentMethod: Value(p.paymentMethod),
              amount: Value(p.amount),
              reference: Value(p.reference),
            ))
        .toList();

    await _db.transaction(() async {
      if (reserveStock) await VariantInventory(_db).reserve(cart);
      await _sales.insertSaleWithItems(
        sale: saleCompanion,
        items: itemCompanions,
        itemOptions: itemOptions,
        payments: paymentCompanions,
      );
    });
  }

}

/// Discriminated union representing the outcome of [SaleRepository.submitSale].
///
/// Use pattern matching to distinguish online (receipt available) from
/// queued (no receipt yet, sale stored locally).
sealed class SaleResult {
  const SaleResult();

  /// Sale was accepted online; [receipt] is ready to display or print.
  const factory SaleResult.online(PosReceiptResponse receipt) = _OnlineResult;

  /// Sale was queued locally; it will be uploaded on the next sync cycle.
  const factory SaleResult.queued() = _QueuedResult;

  /// True when the sale was stored offline (no server receipt yet).
  bool get isQueued => this is _QueuedResult;

  /// The server receipt when the sale went through online, else null.
  PosReceiptResponse? get receiptOrNull {
    final self = this;
    return self is _OnlineResult ? self.receipt : null;
  }
}

/// Online path outcome — carries the server-generated receipt.
class _OnlineResult extends SaleResult {
  final PosReceiptResponse receipt;
  const _OnlineResult(this.receipt);
}

/// Offline path outcome — no receipt available until the sale is uploaded.
class _QueuedResult extends SaleResult {
  const _QueuedResult();
}
