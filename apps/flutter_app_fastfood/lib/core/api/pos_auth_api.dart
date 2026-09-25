import 'package:dio/dio.dart';
import '../models/auth/device_activate_request.dart';
import '../models/auth/device_activate_response.dart';
import '../models/auth/cashier_login_request.dart';
import '../models/auth/cashier_login_response.dart';
import '../models/auth/staff_member.dart';
import '../models/auth/staff_pin_request.dart';
import '../network/api_endpoints.dart';
import '../network/api_exception.dart';

/// HTTP client for the two POS authentication endpoints.
///
/// Token persistence after a successful call is handled by [AuthRepository],
/// not here — this class is responsible only for the network round-trip.
class PosAuthApi {
  final Dio _dio;

  PosAuthApi(this._dio);

  /// Pairs this device using the one-time 4-digit [code] the tenant generated
  /// in the web dashboard (digits only; "58 32" is normalised by the caller).
  ///
  /// Returns [DeviceActivateResponse] with the long-lived device_token plus the
  /// restaurant / branch / currency context. Throws [ApiException] on any error
  /// (422 = invalid / expired / used code).
  Future<DeviceActivateResponse> activate(
    String code, {
    String? platform,
    String? appVersion,
  }) async {
    try {
      final res = await _dio.post(
        ApiEndpoints.activate,
        data: DeviceActivateRequest(
          activationCode: code,
          platform: platform,
          appVersion: appVersion,
        ).toJson(),
      );
      return DeviceActivateResponse.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw e.error is ApiException ? e.error as ApiException : ApiException(message: e.message ?? 'Unknown error');
    }
  }

  /// Authenticates a cashier with [username] and [password].
  ///
  /// Returns [CashierLoginResponse] containing the short-lived cashier_token.
  /// Throws [ApiException] on invalid credentials (401) or connectivity failure.
  Future<CashierLoginResponse> cashierLogin(String username, String password) async {
    try {
      final res = await _dio.post(
        ApiEndpoints.cashierLogin,
        data: CashierLoginRequest(username: username, password: password).toJson(),
      );
      return CashierLoginResponse.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw e.error is ApiException ? e.error as ApiException : ApiException(message: e.message ?? 'Unknown error');
    }
  }

  /// Returns the active staff for this device's branch (device token required).
  ///
  /// Powers the staff-picker grid. Throws [ApiException] on any error.
  Future<List<StaffMember>> listStaff() async {
    try {
      final res = await _dio.get(ApiEndpoints.staffList);
      return (res.data as List)
          .map((e) => StaffMember.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw e.error is ApiException ? e.error as ApiException : ApiException(message: e.message ?? 'Unknown error');
    }
  }

  /// Signs a staff member in with their [pin]. Returns a cashier token.
  ///
  /// Throws [ApiException] with 401 on an invalid PIN.
  Future<CashierLoginResponse> staffPinLogin(String userId, String pin) async {
    try {
      final res = await _dio.post(
        ApiEndpoints.staffPin,
        data: StaffPinRequest(userId: userId, pin: pin).toJson(),
      );
      return CashierLoginResponse.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw e.error is ApiException ? e.error as ApiException : ApiException(message: e.message ?? 'Unknown error');
    }
  }
}
