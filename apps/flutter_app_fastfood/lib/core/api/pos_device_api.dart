import 'package:dio/dio.dart';
import '../network/api_endpoints.dart';
import '../network/api_exception.dart';

/// HTTP client for device-level management endpoints.
///
/// Currently limited to the heartbeat signal which keeps the device record
/// active on the server and allows the back-office to track last-seen times.
class PosDeviceApi {
  final Dio _dio;

  PosDeviceApi(this._dio);

  /// Sends a PATCH heartbeat to inform the server this device is online.
  ///
  /// Should be called periodically (e.g. alongside delta sync). The server
  /// updates the device's last_seen_at timestamp. Throws [ApiException] on error.
  Future<void> heartbeat() async {
    try {
      await _dio.patch(ApiEndpoints.heartbeat);
    } on DioException catch (e) {
      throw e.error is ApiException ? e.error as ApiException : ApiException(message: e.message ?? 'Unknown error');
    }
  }
}
