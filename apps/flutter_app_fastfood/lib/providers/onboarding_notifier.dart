import 'dart:io' show Platform;

import 'package:riverpod_annotation/riverpod_annotation.dart';

import 'auth_notifier.dart';
import 'database_provider.dart';
import 'repository_providers.dart';

part 'onboarding_notifier.g.dart';

/// Snapshot of device activation: is this POS paired, and to which shop/branch.
class OnboardingState {
  final bool onboarded;
  final String? businessName;
  final String? branchId;
  final String? branchName;
  final String? deviceName;
  final String? deviceType;
  final String currency;

  const OnboardingState({
    required this.onboarded,
    this.businessName,
    this.branchId,
    this.branchName,
    this.deviceName,
    this.deviceType,
    this.currency = 'Rs.',
  });

  const OnboardingState.initial()
      : onboarded = false,
        businessName = null,
        branchId = null,
        branchName = null,
        deviceName = null,
        deviceType = null,
        currency = 'Rs.';
}

/// Manages device activation for the app lifetime.
///
/// [build] reads the local settings table; the router redirects to `/activate`
/// whenever [OnboardingState.onboarded] is false.
@Riverpod(keepAlive: true)
class OnboardingNotifier extends _$OnboardingNotifier {
  @override
  Future<OnboardingState> build() async {
    final db = ref.watch(appDatabaseProvider);
    final dao = db.settingsDao;
    final prefs = await ref.watch(sharedPrefsProvider.future);
    final onboarded = await dao.isOnboarded();
    return OnboardingState(
      onboarded: onboarded,
      businessName: await dao.getBusinessName(),
      branchId: await dao.getBranchId(),
      branchName: await dao.getBranchName(),
      deviceName: prefs.getString('device_name'),
      deviceType: prefs.getString('device_type'),
      currency: await dao.getCurrency(),
    );
  }

  /// Pairs this POS with a one-time activation [code].
  ///
  /// On success the device_token is stored (by [AuthRepository]) and the
  /// business / branch / currency context is written locally so the app
  /// skips the activation screen on every later launch.
  Future<void> activate(String code) async {
    final digits = code.replaceAll(RegExp(r'\D'), '');
    final db = ref.read(appDatabaseProvider);
    final prefs = await ref.read(sharedPrefsProvider.future);

    if (await db.settingsDao.isOnboarded()) {
      throw StateError('Deactivate this device before entering a new activation code.');
    }
    await db.clearDeviceData();
    final res = await ref.read(authRepositoryProvider).activateDevice(
          digits,
          platform: Platform.operatingSystem,
        );

    await db.settingsDao.saveOnboarding(
      businessId: res.businessId,
      businessName: res.businessName,
      branchId: res.branchId,
      branchName: res.branchName,
      currency: res.currency,
      deviceLetter: res.deviceLetter,
    );
    await Future.wait([
      prefs.setString('device_id', res.deviceId),
      prefs.setString('branch_id', res.branchId),
      prefs.setString('tenant_id', res.tenantId),
      prefs.setString('device_name', res.deviceName),
      prefs.setString('device_type', res.deviceType),
    ]);

    ref.invalidate(authNotifierProvider);
    state = AsyncData(OnboardingState(
      onboarded: true,
      businessName: res.businessName,
      branchId: res.branchId,
      branchName: res.branchName,
      deviceName: res.deviceName,
      deviceType: res.deviceType,
      currency: res.currency,
    ));
  }

  /// Clears the device token and the local activation record — "Deactivate this
  /// device". Pending sales must be synced before local shop data is cleared.
  Future<void> resetOnboarding() async {
    final db = ref.read(appDatabaseProvider);
    final prefs = await ref.read(sharedPrefsProvider.future);

    await db.clearDeviceData();
    ref.read(authRepositoryProvider).cashierLogout();
    await ref.read(authRepositoryProvider).clearDeviceToken();
    await db.settingsDao.clearOnboarding();
    await Future.wait([
      prefs.remove('device_id'),
      prefs.remove('branch_id'),
      prefs.remove('tenant_id'),
      prefs.remove('device_name'),
      prefs.remove('device_type'),
    ]);

    ref.invalidate(authNotifierProvider);
    state = const AsyncData(OnboardingState.initial());
  }
}
