import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import 'features/activation/activation_screen.dart';
import 'features/activation/device_locked_screen.dart';
import 'features/attendance/attendance_screen.dart';
import 'features/checkout/checkout_screen.dart';
import 'features/checkout/receipt_screen.dart';
import 'features/dashboard/dashboard_screen.dart';
import 'features/dashboard/device_sales_screen.dart';
import 'features/returns/sales_return_screen.dart';
import 'features/pos/pos_screen.dart';
import 'features/settings/settings_screen.dart';
import 'features/shift/shift_close_screen.dart';
import 'features/shift/shift_history_screen.dart';
import 'features/shift/shift_open_screen.dart';
import 'features/staff/staff_screen.dart';
import 'providers/auth_notifier.dart';
import 'providers/dio_provider.dart';
import 'providers/onboarding_notifier.dart';
import 'providers/session_notifier.dart';

part 'app.g.dart';

// ---------------------------------------------------------------------------
// Router
// ---------------------------------------------------------------------------

/// Application router with activation + shift gate redirects.
///
/// Redirect chain on every navigation:
///   1. Not activated (no branch context)  → /activate
///   2. Activated, no staff signed in       → /staff
///   3. Staff signed in, no open shift      → /shift/open
///   4. Staff signed in, open shift         → /dashboard  (/pos reachable)
///
/// [refreshListenable] bumps whenever activation / auth / session state
/// changes so redirects re-run automatically.
@Riverpod(keepAlive: true)
GoRouter router(RouterRef ref) {
  final notifier = ValueNotifier<int>(0);
  ref.listen(onboardingNotifierProvider, (_, __) => notifier.value++);
  ref.listen(authNotifierProvider, (_, __) => notifier.value++);
  ref.listen(sessionNotifierProvider, (_, __) => notifier.value++);
  ref.onDispose(notifier.dispose);

  const activateRoutes = {'/activate'};
  const shiftRoutes = {'/shift/open', '/shift/close'};
  // Attendance clock-in/out never requires (or creates) a cashier session —
  // an employee with a PIN but no pos.operate permission can never become
  // cashier-logged-in, so this route must stay reachable regardless of
  // cashier-login or shift state (device activation is still required).
  const alwaysReachableRoutes = {'/attendance'};

  return GoRouter(
    initialLocation: '/activate',
    refreshListenable: notifier,
    redirect: (context, state) {
      final loc = state.matchedLocation;
      // Shift history is reviewable any time a cashier is signed in —
      // whether or not they currently have a shift open (e.g. right after
      // closing one, before opening the next) — so it's exempted from the
      // "no open shift → /shift/open" redirect below (spec: reviewing a
      // closed shift must never require opening a new one first).
      final isShiftHistoryRoute = loc.startsWith('/shift-history');

      final onboarding = ref.read(onboardingNotifierProvider).valueOrNull;
      final auth = ref.read(authNotifierProvider).valueOrNull;
      if (onboarding == null || auth == null) return null; // still loading

      // 1. Activation.
      if (!onboarding.onboarded) {
        return activateRoutes.contains(loc) ? null : '/activate';
      }

      // 2. Staff sign-in.
      if (!auth.isCashierLoggedIn) {
        return (loc == '/staff' || alwaysReachableRoutes.contains(loc))
            ? null
            : '/staff';
      }

      // 3. Open shift.
      final session = ref.read(sessionNotifierProvider).valueOrNull;
      if (session == null) {
        return (shiftRoutes.contains(loc) ||
                isShiftHistoryRoute ||
                alwaysReachableRoutes.contains(loc))
            ? null
            : '/shift/open';
      }

      // 4. Fully in — bounce away from the gate screens.
      if (activateRoutes.contains(loc) ||
          loc == '/staff' ||
          loc == '/shift/open') {
        return '/dashboard';
      }
      return null;
    },
    routes: [
      GoRoute(
        path: '/activate',
        builder: (_, __) => const ActivationScreen(),
      ),
      GoRoute(path: '/staff', builder: (_, __) => const StaffScreen()),
      GoRoute(
          path: '/attendance', builder: (_, __) => const AttendanceScreen()),
      GoRoute(path: '/shift/open', builder: (_, __) => const ShiftOpenScreen()),
      GoRoute(
          path: '/shift/close', builder: (_, __) => const ShiftCloseScreen()),
      GoRoute(
        path: '/shift-history',
        builder: (_, __) => const ShiftHistoryScreen(),
      ),
      GoRoute(
        path: '/shift-history/:id',
        builder: (_, state) => ShiftHistoryDetailScreen(
          sessionId: state.pathParameters['id']!,
        ),
      ),
      GoRoute(path: '/dashboard', builder: (_, __) => const DashboardScreen()),
      GoRoute(
        path: '/sales',
        builder: (_, state) => DeviceSalesScreen(
          report: state.uri.queryParameters['report'] == '1',
        ),
      ),
      GoRoute(path: '/returns', builder: (_, __) => const SalesReturnScreen()),
      GoRoute(path: '/settings', builder: (_, __) => const SettingsScreen()),
      GoRoute(path: '/pos', builder: (_, __) => const PosScreen()),
      GoRoute(
          path: '/pos/checkout', builder: (_, __) => const CheckoutScreen()),
      GoRoute(
        path: '/pos/receipt/:id',
        builder: (_, state) =>
            ReceiptScreen(saleId: state.pathParameters['id']!),
      ),
    ],
  );
}

// ---------------------------------------------------------------------------
// App shell
// ---------------------------------------------------------------------------

/// Root MaterialApp.router driven by [routerProvider], with a device-lock
/// overlay driven by [deviceLockProvider].
class FastFoodPosApp extends ConsumerWidget {
  const FastFoodPosApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);

    // A missing, revoked, or invalid/expired device token means the saved local
    // activation can no longer authenticate. Clear it and return to activation.
    // A suspended device remains paired and uses the lock overlay below.
    ref.listen<String?>(deviceLockProvider, (_, code) async {
      if (code == 'DEVICE_REVOKED' ||
          code == 'DEVICE_NOT_FOUND' ||
          code == 'DEVICE_TOKEN_INVALID') {
        await ref.read(onboardingNotifierProvider.notifier).resetOnboarding();
        router.go('/activate');
        ref.read(deviceLockProvider.notifier).clear();
      }
    });

    return MaterialApp.router(
      title: 'STORIXX',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFFE65100)),
        useMaterial3: true,
      ),
      routerConfig: router,
      builder: (context, child) {
        final lock = ref.watch(deviceLockProvider);
        if (lock == 'DEVICE_SUSPENDED') {
          return DeviceLockedScreen(
            onRetry: () => ref.read(deviceLockProvider.notifier).clear(),
          );
        }
        return child ?? const SizedBox.shrink();
      },
    );
  }
}
