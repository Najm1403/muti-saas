import 'package:flutter/foundation.dart';
import 'package:dio/dio.dart';
import '../security/token_storage.dart';
import 'api_exception.dart';

/// Base URL injected at build time via --dart-define=API_URL=https://...
/// Falls back to the Android emulator loopback when not set.
const _apiUrl =
    String.fromEnvironment('API_URL', defaultValue: 'http://10.0.2.2:8000');

/// Public form of the API base URL, for building absolute URLs to server assets
/// (e.g. product images whose `image_path` is stored relative: `/media/...`).
const String apiBaseUrl = _apiUrl;

/// Device-scoped routes must keep using the persistent device token even when
/// a cashier token exists. All sale/session/upload routes use the cashier token.
bool usesDeviceTokenForPath(String path) {
  const deviceRoutes = {
    '/api/v1/pos/auth/cashier',
    '/api/v1/pos/auth/staff',
    '/api/v1/pos/auth/staff-pin',
    '/api/v1/pos/sync/full',
    '/api/v1/pos/sync/delta',
    '/api/v1/pos/device/heartbeat',
    // Attendance never requires (or creates) a cashier session — an
    // attendance-only employee with a PIN but no pos.operate permission
    // must still be able to clock in/out from the staff picker.
    '/api/v1/pos/attendance/staff',
    '/api/v1/pos/attendance/punch',
    '/api/v1/pos/attendance/status',
  };
  return deviceRoutes.contains(Uri.parse(path).path);
}

/// Resolves a possibly-relative server path to an absolute URL.
/// Returns null for empty input; passes through values that are already absolute.
String? assetUrl(String? path) {
  if (path == null || path.isEmpty) return null;
  if (path.startsWith('http://') || path.startsWith('https://')) return path;
  return '$apiBaseUrl${path.startsWith('/') ? '' : '/'}$path';
}

/// Constructs and configures the shared [Dio] instance used by all API services.
///
/// Attaches [_TokenInterceptor] to inject the appropriate auth header and
/// [_ErrorInterceptor] to normalize all HTTP errors into [ApiException].
Dio buildDio(TokenStorage tokens, {void Function(String code)? onDeviceLock}) {
  if (kReleaseMode &&
      (!const bool.hasEnvironment('API_URL') ||
          Uri.tryParse(_apiUrl)?.scheme != 'https')) {
    throw StateError('Release builds require an explicit HTTPS API_URL.');
  }
  final dio = Dio(
    BaseOptions(
      baseUrl: _apiUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 30),
      headers: {'Content-Type': 'application/json'},
    ),
  );

  dio.interceptors.add(_TokenInterceptor(tokens));
  dio.interceptors.add(_ErrorInterceptor(onDeviceLock));

  return dio;
}

/// Injects the correct Bearer token on every outgoing request.
///
/// Cashier token takes priority because it is shorter-lived and more
/// specific. The device token is used only for pre-login endpoints
/// (activate, cashier-login) where no cashier token exists yet.
class _TokenInterceptor extends Interceptor {
  final TokenStorage _tokens;

  _TokenInterceptor(this._tokens);

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final cashier = _tokens.cashierToken;
    if (cashier != null && !usesDeviceTokenForPath(options.path)) {
      options.headers['Authorization'] = 'Bearer $cashier';
      return handler.next(options);
    }
    // Fall back to device token for activate/cashier-login endpoints.
    _tokens.getDeviceToken().then((device) {
      if (device != null) {
        options.headers['Authorization'] = 'Bearer $device';
      }
      handler.next(options);
    });
  }
}

/// Converts every [DioException] into an [ApiException] with a human-readable message.
///
/// Handles both FastAPI-style validation error lists and plain string detail fields
/// so callers always receive a consistent error type regardless of server format.
class _ErrorInterceptor extends Interceptor {
  final void Function(String code)? _onDeviceLock;

  _ErrorInterceptor(this._onDeviceLock);

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    final response = err.response;
    if (response == null) {
      // A missing response means the configured API could not be reached. It
      // does not necessarily mean public internet is unavailable: desktop
      // development commonly targets a backend on 127.0.0.1.
      return handler.next(
        err.copyWith(
          error: const ApiException(
            message: 'Cannot reach the POS server at $_apiUrl. '
                'Check that the backend is running and API_URL is correct.',
          ),
        ),
      );
    }

    final body = response.data;
    String message = 'Request failed';
    String? code;
    Map<String, dynamic>? detail;

    if (body is Map<String, dynamic>) {
      code = body['code'] as String?;
      final d = body['detail'];
      if (d is String) {
        message = d;
      } else if (d is List && d.isNotEmpty) {
        // FastAPI validation errors return a list; use the first message.
        message = (d.first['msg'] as String?) ?? message;
        detail = body;
      } else {
        detail = body;
      }
    }

    // Device was suspended / revoked server-side — notify the app shell so it
    // Lifecycle failures let the app lock the UI or clear stale activation.
    const deviceLifecycleCodes = {
      'DEVICE_SUSPENDED',
      'DEVICE_REVOKED',
      'DEVICE_NOT_FOUND',
      'DEVICE_TOKEN_INVALID',
    };
    if (deviceLifecycleCodes.contains(code)) {
      _onDeviceLock?.call(code!);
    }

    handler.next(
      err.copyWith(
        error: ApiException(
          statusCode: response.statusCode,
          message: message,
          code: code,
          detail: detail,
        ),
      ),
    );
  }
}
