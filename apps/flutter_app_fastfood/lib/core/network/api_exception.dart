/// Typed exception thrown by all API service classes instead of raw [DioException].
///
/// [_ErrorInterceptor] in [buildDio] converts every Dio error into an
/// [ApiException] so callers can switch on status codes without importing Dio.
/// [statusCode] is null when there was no HTTP response (i.e. the device is offline).
class ApiException implements Exception {
  final int? statusCode;
  final String message;

  /// Machine-readable error code from the server body, when present
  /// (e.g. "DEVICE_SUSPENDED", "DEVICE_REVOKED").
  final String? code;

  /// Raw server error body for structured validation errors; null for simple messages.
  final Map<String, dynamic>? detail;

  const ApiException({
    this.statusCode,
    required this.message,
    this.code,
    this.detail,
  });

  /// True when the server returned 401 — cashier token has expired or is invalid.
  bool get isUnauthorized => statusCode == 401;

  /// True when the server returned 403 — action not permitted for this device/role.
  bool get isForbidden => statusCode == 403;

  bool get isNotFound => statusCode == 404;

  /// True when the server returned 409 — typically a duplicate sale_number.
  bool get isConflict => statusCode == 409;

  /// True when [statusCode] is null, meaning no network response was received.
  bool get isOffline => statusCode == null;

  @override
  String toString() => 'ApiException($statusCode): $message';
}
