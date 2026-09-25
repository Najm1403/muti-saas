import 'package:dio/dio.dart';
import '../models/sync/pos_sync_response.dart';
import '../models/sync/pos_delta_sync_response.dart';
import '../models/sync/pos_upload_request.dart';
import '../models/sync/pos_upload_response.dart';
import '../network/api_endpoints.dart';
import '../network/api_exception.dart';

/// HTTP client for the three POS catalog sync endpoints.
///
/// Orchestration logic (deciding full vs delta, updating the last_sync_at
/// cursor) lives in [SyncRepository] — this class handles only the network calls.
class PosSyncApi {
  final Dio _dio;

  PosSyncApi(this._dio);

  /// Downloads the complete menu catalog for this branch.
  ///
  /// Used on first launch and whenever a forced re-sync is triggered.
  /// Throws [ApiException] on connectivity or server errors.
  Future<PosSyncResponse> fullSync() async {
    try {
      final res = await _dio.get(ApiEndpoints.fullSync);
      return PosSyncResponse.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw e.error is ApiException ? e.error as ApiException : ApiException(message: e.message ?? 'Unknown error');
    }
  }

  /// Downloads only catalog records modified after [since].
  ///
  /// [since] is sent as a UTC ISO-8601 string so the server can filter
  /// by its updated_at index. Throws [ApiException] on error.
  Future<PosDeltaSyncResponse> deltaSync(DateTime since) async {
    try {
      final res = await _dio.get(
        ApiEndpoints.deltaSync,
        queryParameters: {'since': since.toUtc().toIso8601String()},
      );
      return PosDeltaSyncResponse.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw e.error is ApiException ? e.error as ApiException : ApiException(message: e.message ?? 'Unknown error');
    }
  }

  /// Uploads a batch of offline-queued sales to the server.
  ///
  /// Returns [PosUploadResponse] with per-sale results so the caller can
  /// mark individual sales as synced or flag failures. Throws [ApiException] on error.
  Future<PosUploadResponse> uploadOffline(PosUploadRequest request) async {
    try {
      final res = await _dio.post(
        ApiEndpoints.uploadOffline,
        data: request.toJson(),
      );
      return PosUploadResponse.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw e.error is ApiException ? e.error as ApiException : ApiException(message: e.message ?? 'Unknown error');
    }
  }
}
