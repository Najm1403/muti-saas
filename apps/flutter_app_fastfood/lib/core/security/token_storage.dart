import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Manages the two auth token lifetimes used by the POS.
///
/// device_token (30-day) is encrypted on disk via [FlutterSecureStorage] so it
/// survives app restarts — a device stays activated until the token expires.
/// cashier_token (12-hour) is kept in memory only; it is automatically cleared
/// on app restart, enforcing that cashiers must re-login each new session.
class TokenStorage {
  static const _deviceKey = 'device_token';

  final FlutterSecureStorage _store;

  /// In-memory only — never written to disk for security.
  String? _cashierToken;
  String? offlineProof;

  TokenStorage({FlutterSecureStorage? store})
      : _store = store ??
            const FlutterSecureStorage(
              // Uses Android EncryptedSharedPreferences for AES-256 at rest.
              aOptions: AndroidOptions(encryptedSharedPreferences: true),
            );

  /// Reads the persisted device token from encrypted storage.
  Future<String?> getDeviceToken() => _store.read(key: _deviceKey);

  /// Persists the device token after a successful activation.
  Future<void> saveDeviceToken(String token) =>
      _store.write(key: _deviceKey, value: token);

  /// Removes the device token, forcing the device through re-activation.
  Future<void> clearDeviceToken() => _store.delete(key: _deviceKey);

  /// Returns the in-memory cashier token; null if no cashier is logged in.
  String? get cashierToken => _cashierToken;

  /// Stores the cashier token in memory only — never persisted to disk.
  void saveCashierToken(String token) => _cashierToken = token;

  /// Clears the cashier token to log the current cashier out.
  void clearCashierToken() { _cashierToken = null; offlineProof = null; }

  /// Clears the cashier session without touching the device token.
  ///
  /// Device token is cleared separately to allow the same device to be
  /// re-used across cashier logins without requiring re-activation.
  void clearAll() {
    _cashierToken = null;
    offlineProof = null;
  }
}
