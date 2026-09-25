import 'dart:async';
import 'package:decimal/decimal.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'auth_notifier.dart';
import 'connectivity_provider.dart';
import 'dio_provider.dart';

/// The active cashier's manual-discount eligibility and cap, from
/// `/api/v1/pos/auth/payment-permissions` (backend: the `sales.discount`
/// permission gates [eligible]; `User.max_discount_percent` sets [maxPercent]
/// — null means uncapped). Fail closed on any error.
class DiscountPermission {
  final bool eligible;
  final Decimal? maxPercent;
  const DiscountPermission({required this.eligible, this.maxPercent});
  static const denied = DiscountPermission(eligible: false);
}

/// Rechecked periodically while the cart/checkout screen is open so a
/// revoked permission or lowered cap takes effect without a fresh login.
final discountPermissionProvider =
    FutureProvider.autoDispose<DiscountPermission>((ref) async {
  final auth = ref.watch(authNotifierProvider).valueOrNull;
  final online = ref.watch(connectivityProvider).valueOrNull ?? false;
  if (!online || auth == null || !auth.isCashierLoggedIn) {
    return DiscountPermission.denied;
  }
  final timer = Timer(const Duration(seconds: 15), ref.invalidateSelf);
  ref.onDispose(timer.cancel);
  try {
    final response =
        await ref.read(dioProvider).get('/api/v1/pos/auth/payment-permissions');
    final eligible = response.data['can_give_discount'] == true;
    final rawCap = response.data['max_discount_percent'];
    return DiscountPermission(
      eligible: eligible,
      maxPercent: rawCap == null ? null : Decimal.parse(rawCap.toString()),
    );
  } catch (_) {
    return DiscountPermission.denied;
  }
});

/// Convenience bool view for widgets that only need visibility, not the cap.
final discountEligibilityProvider = FutureProvider.autoDispose<bool>((ref) async {
  return (await ref.watch(discountPermissionProvider.future)).eligible;
});
