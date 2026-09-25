import '../../core/api/pos_auth_api.dart';
import '../../core/models/auth/cashier_login_response.dart';
import '../../core/models/auth/device_activate_response.dart';
import '../../core/models/auth/staff_member.dart';
import '../../core/security/token_storage.dart';

/// Orchestrates device activation and cashier authentication.
///
/// Sits between the UI and [PosAuthApi], taking care of persisting tokens
/// to [TokenStorage] after each successful network call so callers don't
/// need to know which token goes where.
class AuthRepository {
  final PosAuthApi _api;
  final TokenStorage _tokens;

  AuthRepository(this._api, this._tokens);

  /// Pairs this device with the one-time activation [code] and persists the
  /// device_token to encrypted storage.
  ///
  /// Returns the full [DeviceActivateResponse] so the caller can store the
  /// restaurant / branch / currency context.
  Future<DeviceActivateResponse> activateDevice(
    String code, {
    String? platform,
    String? appVersion,
  }) async {
    final res = await _api.activate(code, platform: platform, appVersion: appVersion);
    await _tokens.saveDeviceToken(res.deviceToken);
    return res;
  }

  /// Authenticates [username]/[password] and holds the cashier_token in memory.
  ///
  /// The cashier_token is intentionally not persisted — it clears on app restart
  /// to enforce that every shift starts with an explicit login.
  Future<CashierLoginResponse> cashierLogin(String username, String password) async {
    final res = await _api.cashierLogin(username, password);
    _tokens.saveCashierToken(res.cashierToken);
    _tokens.offlineProof = res.offlineProof;
    return res;
  }

  /// Signs a staff member in from the staff picker with their [pin].
  ///
  /// Like [cashierLogin] the cashier_token is held in memory only.
  Future<CashierLoginResponse> staffLoginWithPin(String userId, String pin) async {
    final res = await _api.staffPinLogin(userId, pin);
    _tokens.saveCashierToken(res.cashierToken);
    _tokens.offlineProof = res.offlineProof;
    return res;
  }

  /// Lists the active staff for this device's branch (device token required).
  Future<List<StaffMember>> listStaff() => _api.listStaff();

  /// Clears the in-memory cashier_token, effectively ending the cashier's session.
  void cashierLogout() => _tokens.clearCashierToken();

  /// Removes the persisted device_token — used when deactivating / revoking the device.
  Future<void> clearDeviceToken() => _tokens.clearDeviceToken();

  /// True when a device_token is present in encrypted storage.
  ///
  /// Used on startup to skip the activation screen for already-activated devices.
  Future<bool> get isDeviceActivated async =>
      (await _tokens.getDeviceToken()) != null;

  /// True when a cashier_token is held in memory (cashier is signed in).
  bool get isCashierLoggedIn => _tokens.cashierToken != null;
}
