import 'package:dio/dio.dart';
import '../models/sale/pos_sale_create.dart';
import '../models/sale/pos_receipt_response.dart';
import '../network/api_endpoints.dart';
import '../network/api_exception.dart';

/// HTTP client for the POS sale creation and receipt endpoints.
///
/// Only called when the device is online. Offline sale queuing is
/// handled by [SaleRepository] before this class is reached.
class PosSaleApi {
  final Dio _dio;

  PosSaleApi(this._dio);

  /// Submits a completed sale to the server and returns the receipt.
  ///
  /// [data] carries the full sale including items, options, and payments.
  /// Throws [ApiException] on server validation errors or connectivity loss.
  Future<PosReceiptResponse> createSale(PosSaleCreate data) async {
    try {
      final res = await _dio.post(
        ApiEndpoints.createSale,
        data: data.toJson(),
      );
      return PosReceiptResponse.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw e.error is ApiException
          ? e.error as ApiException
          : ApiException(message: e.message ?? 'Unknown error');
    }
  }

  /// Fetches the receipt for one of the calling cashier's *own* sales.
  ///
  /// Returns 404 if [saleId] exists but belongs to a different cashier.
  /// Use [getReceiptByNumber] to explicitly reprint another cashier's sale.
  Future<PosReceiptResponse> getReceipt(String saleId) async {
    try {
      final res = await _dio.get(ApiEndpoints.receiptById(saleId));
      return PosReceiptResponse.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw e.error is ApiException
          ? e.error as ApiException
          : ApiException(message: e.message ?? 'Unknown error');
    }
  }

  /// Looks up any completed sale in the branch by its human-readable [saleNumber].
  ///
  /// Unlike [getReceipt], this is not restricted to the calling cashier's own sales.
  /// The Flutter UI must show a confirmation screen (sale summary + cashier name)
  /// before proceeding to print, so the cashier explicitly acknowledges they are
  /// reprinting a sale that belongs to a colleague.
  ///
  /// Throws [ApiException] with 404 if no sale with [saleNumber] exists in the branch.
  Future<PosReceiptResponse> getReceiptByNumber(String saleNumber) async {
    try {
      final res = await _dio.get(ApiEndpoints.receiptByNumber(saleNumber));
      return PosReceiptResponse.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw e.error is ApiException
          ? e.error as ApiException
          : ApiException(message: e.message ?? 'Unknown error');
    }
  }

  Future<List<PosReceiptResponse>> recentSales({
    int limit = 20,
    DateTime? dateFrom,
    DateTime? dateTo,
    String? sessionId,
  }) async {
    try {
      final res = await _dio.get(ApiEndpoints.recentSales, queryParameters: {
        'limit': limit,
        if (dateFrom != null) 'date_from': dateFrom.toUtc().toIso8601String(),
        if (dateTo != null) 'date_to': dateTo.toUtc().toIso8601String(),
        if (sessionId != null) 'session_id': sessionId,
      });
      return (res.data as List<dynamic>)
          .map((e) => PosReceiptResponse.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw e.error is ApiException
          ? e.error as ApiException
          : ApiException(message: e.message ?? 'Unknown error');
    }
  }

  Future<Map<String, dynamic>> cancelSale(String saleId, String reason) async {
    try {
      final res = await _dio
          .post(ApiEndpoints.cancelSale(saleId), data: {'reason': reason});
      return Map<String, dynamic>.from(res.data as Map);
    } on DioException catch (e) {
      throw e.error is ApiException
          ? e.error as ApiException
          : ApiException(message: e.message ?? 'Unknown error');
    }
  }

  Future<Map<String, dynamic>> returnItems(
      String saleId, List<Map<String, dynamic>> items, String? reason) async {
    try {
      final res = await _dio.post(ApiEndpoints.returnSale(saleId), data: {
        'reason': reason?.trim().isEmpty == true ? null : reason?.trim(),
        'items': items,
      });
      return Map<String, dynamic>.from(res.data as Map);
    } on DioException catch (e) {
      throw e.error is ApiException
          ? e.error as ApiException
          : ApiException(message: e.message ?? 'Unknown error');
    }
  }
}
