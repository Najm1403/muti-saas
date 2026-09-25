import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../features/pos/pos_state.dart';
import 'database_provider.dart';
import 'repository_providers.dart';

part 'auth_notifier.g.dart';

/// Immutable snapshot of device activation and cashier login state.
///
/// Produced by [AuthNotifier.build] on startup by reading encrypted storage
/// and SharedPreferences. Mutated only through the notifier's action methods.
class AuthState {
  final bool isDeviceActivated;
  final String? deviceId;
  final String? branchId;
  final String? tenantId;
  final String? deviceName;
  final bool isCashierLoggedIn;
  final String? cashierName;
  final String? userId;

  const AuthState({
    required this.isDeviceActivated,
    this.deviceId,
    this.branchId,
    this.tenantId,
    this.deviceName,
    required this.isCashierLoggedIn,
    this.cashierName,
    this.userId,
  });

  const AuthState.initial()
      : isDeviceActivated = false,
        deviceId = null,
        branchId = null,
        tenantId = null,
        deviceName = null,
        isCashierLoggedIn = false,
        cashierName = null,
        userId = null;

  AuthState copyWith({
    bool? isDeviceActivated,
    String? deviceId,
    String? branchId,
    String? tenantId,
    String? deviceName,
    bool? isCashierLoggedIn,
    String? cashierName,
    String? userId,
  }) =>
      AuthState(
        isDeviceActivated: isDeviceActivated ?? this.isDeviceActivated,
        deviceId: deviceId ?? this.deviceId,
        branchId: branchId ?? this.branchId,
        tenantId: tenantId ?? this.tenantId,
        deviceName: deviceName ?? this.deviceName,
        isCashierLoggedIn: isCashierLoggedIn ?? this.isCashierLoggedIn,
        cashierName: cashierName ?? this.cashierName,
        userId: userId ?? this.userId,
      );
}

/// Manages device activation and cashier login state for the entire app lifetime.
///
/// [build] reads encrypted storage + SharedPreferences to reconstruct persisted
/// state on startup. Cashier identity is always in-memory — [cashierLogout]
/// clears it without touching disk.
@Riverpod(keepAlive: true)
class AuthNotifier extends _$AuthNotifier {
  @override
  Future<AuthState> build() async {
    final repo = ref.watch(authRepositoryProvider);
    final prefs = await ref.watch(sharedPrefsProvider.future);

    final isActivated = await repo.isDeviceActivated;
    return AuthState(
      isDeviceActivated: isActivated,
      deviceId: prefs.getString('device_id'),
      branchId: prefs.getString('branch_id'),
      tenantId: prefs.getString('tenant_id'),
      deviceName: prefs.getString('device_name'),
      isCashierLoggedIn: repo.isCashierLoggedIn,
    );
  }

  /// Authenticates the cashier and stores the token in memory only.
  ///
  /// The cashier_token is intentionally not persisted — it clears on restart
  /// so every shift starts with an explicit login. Router will redirect to /pos
  /// once [isCashierLoggedIn] is true.
  Future<void> cashierLogin(String username, String password) async {
    final repo = ref.read(authRepositoryProvider);
    final current = state.valueOrNull ?? const AuthState.initial();

    final res = await repo.cashierLogin(username, password);
    state = AsyncData(current.copyWith(
      isCashierLoggedIn: true,
      cashierName: res.fullName,
      userId: res.userId,
    ));
  }

  /// Signs a staff member in from the staff-picker grid with their PIN.
  ///
  /// Stores the cashier token in memory only (clears on restart). The router
  /// then routes to `/shift/open` or `/dashboard` based on the session state.
  Future<void> staffLoginWithPin(String userId, String pin) async {
    final repo = ref.read(authRepositoryProvider);
    final current = state.valueOrNull ?? const AuthState.initial();

    final res = await repo.staffLoginWithPin(userId, pin);
    state = AsyncData(current.copyWith(
      isCashierLoggedIn: true,
      cashierName: res.fullName,
      userId: res.userId,
    ));
  }

  /// Clears the in-memory cashier token, ending the current shift.
  ///
  /// The device remains activated — only the cashier identity is removed.
  /// Also clears the shared cart and POS category/product selection: both
  /// are process-wide singletons, not per-cashier state, so without this a
  /// cashier logging in next would inherit whatever the previous cashier
  /// left mid-order (an abandoned cart, or a half-picked product).
  void cashierLogout() {
    ref.read(authRepositoryProvider).cashierLogout();
    ref.read(posNotifierProvider.notifier).resetAll();
    final current = state.valueOrNull ?? const AuthState.initial();
    state = AsyncData(current.copyWith(
      isCashierLoggedIn: false,
      cashierName: null,
      userId: null,
    ));
    // cartServiceProvider watches this notifier's (userId, branchId) — see
    // repository_providers.dart — so setting userId to null above already
    // tears down the old CartService instance and replaces it with a fresh,
    // empty one; a second, explicit ref.read(cartServiceProvider).clear()
    // used to live here, but reading a provider that itself watches this
    // exact notifier, from inside this notifier's own method, is a circular
    // dependency Riverpod actively rejects (CircularDependencyError) —
    // it surfaced intermittently depending on the surrounding rebuild
    // timing (e.g. right after closing a shift, mid-redirect-cascade),
    // crashing cashierLogout() before it could ever reach this state
    // update. The reactive watch alone already covers both the logout
    // case (userId -> null) and the "different cashier logs in without an
    // explicit prior logout" case (userId -> the new cashier's id) that it
    // was originally added for.
  }
}
