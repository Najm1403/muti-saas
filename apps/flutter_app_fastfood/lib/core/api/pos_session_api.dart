import 'package:dio/dio.dart';
import '../models/session/session_open_request.dart';
import '../models/session/session_close_request.dart';
import '../models/session/session_close_response.dart';
import '../models/session/session_response.dart';
import '../models/session/session_summary_response.dart';
import '../network/api_endpoints.dart';
import '../network/api_exception.dart';

/// HTTP client for the cashier session lifecycle endpoints.
///
/// Sessions track shift start/end times and cash drawer counts per device.
/// All three operations require a valid cashier_token in the Authorization header.
class PosSessionApi {
  final Dio _dio;

  PosSessionApi(this._dio);

  /// Opens a new shift session for the authenticated cashier on this device.
  ///
  /// Returns the created [SessionResponse]. Throws [ApiException] if a session
  /// is already open on this device (server returns 409).
  Future<SessionResponse> openSession(SessionOpenRequest data) async {
    try {
      final res = await _dio.post(ApiEndpoints.openSession, data: data.toJson());
      return SessionResponse.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw e.error is ApiException ? e.error as ApiException : ApiException(message: e.message ?? 'Unknown error');
    }
  }

  /// Closes the current shift session with the given [data] (closing cash count).
  ///
  /// Returns the [SessionCloseResponse] — the closed session, the shift
  /// reconciliation summary, and the cash variance.
  /// Throws [ApiException] if no open session exists (404).
  Future<SessionCloseResponse> closeSession(SessionCloseRequest data) async {
    try {
      final res = await _dio.post(ApiEndpoints.closeSession, data: data.toJson());
      return SessionCloseResponse.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw e.error is ApiException ? e.error as ApiException : ApiException(message: e.message ?? 'Unknown error');
    }
  }

  /// Returns the currently open session for this device, if any.
  ///
  /// Throws [ApiException] with 404 when no session is open — callers
  /// should handle this to prompt the cashier to open a session.
  Future<SessionResponse> currentSession() async {
    try {
      final res = await _dio.get(ApiEndpoints.currentSession);
      return SessionResponse.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw e.error is ApiException ? e.error as ApiException : ApiException(message: e.message ?? 'Unknown error');
    }
  }

  /// Returns the current shift's live reconciliation summary.
  ///
  /// Throws [ApiException] with 404 when no session is open.
  Future<SessionSummaryResponse> sessionSummary() async {
    try {
      final res = await _dio.get(ApiEndpoints.sessionSummary);
      return SessionSummaryResponse.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw e.error is ApiException ? e.error as ApiException : ApiException(message: e.message ?? 'Unknown error');
    }
  }

  /// Returns this cashier's past (closed) shifts, newest first.
  Future<List<SessionResponse>> history() async {
    try {
      final res = await _dio.get(ApiEndpoints.sessionHistory);
      return (res.data as List)
          .map((e) => SessionResponse.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw e.error is ApiException ? e.error as ApiException : ApiException(message: e.message ?? 'Unknown error');
    }
  }

  /// Returns the full reconciliation summary for one past shift by [sessionId].
  ///
  /// Works for a closed session (unlike [sessionSummary], which requires an
  /// open one) — this is how a cashier reviews a shift after closing it.
  Future<SessionSummaryResponse> historySummary(String sessionId) async {
    try {
      final res = await _dio.get(ApiEndpoints.sessionHistorySummary(sessionId));
      return SessionSummaryResponse.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw e.error is ApiException ? e.error as ApiException : ApiException(message: e.message ?? 'Unknown error');
    }
  }
}
