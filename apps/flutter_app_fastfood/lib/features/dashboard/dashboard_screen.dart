// features/dashboard/dashboard_screen.dart
//
// Post-login hub. New Order, shift status, settings gear, close shift, logout.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../providers/auth_notifier.dart';
import '../../providers/currency_provider.dart';
import '../../providers/onboarding_notifier.dart';
import '../../providers/session_notifier.dart';
import '../../providers/menu_provider.dart';
import '../pos/pos_theme.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authNotifierProvider).valueOrNull;
    final onboarding = ref.watch(onboardingNotifierProvider).valueOrNull;
    final session = ref.watch(sessionNotifierProvider).valueOrNull;
    final money = ref.watch(moneyProvider);
    final lowStockCount = ref.watch(lowStockCountProvider).valueOrNull ?? 0;
    final lowStockThreshold =
        ref.watch(lowStockThresholdProvider).valueOrNull ?? 5;

    return Scaffold(
      backgroundColor: PosTheme.bg,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Hi, ${auth?.cashierName ?? 'there'}',
                        style: const TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.w800,
                            color: PosTheme.text),
                      ),
                      Text(
                        '${onboarding?.businessName ?? ''}'
                        '${onboarding?.branchName != null ? ' · ${onboarding!.branchName}' : ''}',
                        style: const TextStyle(
                            fontSize: 12, color: PosTheme.textMuted),
                      ),
                    ],
                  ),
                  const Spacer(),
                  IconButton(
                    onPressed: () => context.push('/attendance'),
                    icon: const Icon(Icons.badge_outlined,
                        color: PosTheme.text),
                    tooltip: 'Clock In / Out',
                  ),
                  IconButton(
                    onPressed: () => context.push('/settings'),
                    icon: const Icon(Icons.settings_outlined,
                        color: PosTheme.text),
                    tooltip: 'Settings',
                  ),
                ],
              ),
              const SizedBox(height: 16),
              if (lowStockCount > 0) ...[
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFFF7ED),
                    borderRadius: BorderRadius.circular(18),
                    border: Border.all(color: const Color(0xFFFED7AA)),
                  ),
                  child: Row(children: [
                    const Icon(Icons.inventory_2_outlined,
                        size: 18, color: Color(0xFFC2410C)),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        '$lowStockCount tracked item${lowStockCount == 1 ? '' : 's'} at or below $lowStockThreshold in this branch.',
                        style: const TextStyle(
                            fontSize: 12.5, color: Color(0xFF9A3412)),
                      ),
                    ),
                  ]),
                ),
                const SizedBox(height: 12),
              ],
              if (session != null)
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: PosTheme.accent2Light,
                    borderRadius: BorderRadius.circular(18),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.lock_clock,
                          size: 18, color: PosTheme.accent2Text),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          '${session.shiftNumber != null ? 'Shift ${session.shiftNumber} · open since ' : 'Shift open since '}'
                          '${TimeOfDay.fromDateTime(session.openedAt.toLocal()).format(context)}'
                          '  ·  opening ${money(session.openingCash)}',
                          style: const TextStyle(
                              fontSize: 12.5, color: PosTheme.accent2Text),
                        ),
                      ),
                    ],
                  ),
                ),
              const SizedBox(height: 20),
              _BigAction(
                label: 'New Order',
                icon: Icons.add_shopping_cart,
                onTap: () => context.push('/pos'),
              ),
              const SizedBox(height: 14),
              Row(
                children: [
                  Expanded(
                    child: _Tile(
                      label: 'Sales Return',
                      icon: Icons.assignment_return_outlined,
                      onTap: () => context.push('/returns'),
                    ),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: _Tile(
                      label: 'Sales',
                      icon: Icons.receipt_long_outlined,
                      onTap: () => context.push('/sales'),
                    ),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: _Tile(
                      label: 'Reports',
                      icon: Icons.bar_chart_outlined,
                      onTap: () => context.push('/sales?report=1'),
                    ),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: _Tile(
                      label: 'Shift History',
                      icon: Icons.history,
                      onTap: () => context.push('/shift-history'),
                    ),
                  ),
                ],
              ),
              const Spacer(),
              OutlinedButton.icon(
                // go(), not push(): closing the shift flips the session to
                // null while this screen is showing, which fires the
                // router's refreshListenable mid-flow. With push(), that
                // re-evaluation resolves the redirect's "current location"
                // against the underlying /dashboard route rather than this
                // pushed /shift/close screen — /dashboard isn't exempt from
                // the "no open shift" redirect, so it got yanked straight
                // to /shift/open (reopen as the same cashier) before the
                // close flow's own post-close navigation ever ran. go()
                // makes /shift/close the actual top-level matched route, so
                // the redirect re-evaluates correctly against it instead.
                onPressed: () => context.go('/shift/close'),
                icon: const Icon(Icons.point_of_sale, size: 18),
                style: OutlinedButton.styleFrom(
                  foregroundColor: PosTheme.text,
                  side: const BorderSide(color: PosTheme.divider, width: 2),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: const RoundedRectangleBorder(
                      borderRadius: PosTheme.pillRadius),
                ),
                label: const Text('Close shift'),
              ),
              const SizedBox(height: 10),
              TextButton.icon(
                onPressed: () {
                  ref.read(authNotifierProvider.notifier).cashierLogout();
                  context.go('/staff');
                },
                icon: const Icon(Icons.logout, size: 18),
                label: const Text('Log out'),
                style:
                    TextButton.styleFrom(foregroundColor: PosTheme.textMuted),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _BigAction extends StatelessWidget {
  final String label;
  final IconData icon;
  final VoidCallback onTap;
  const _BigAction(
      {required this.label, required this.icon, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: 92,
        decoration: BoxDecoration(
          color: PosTheme.accent,
          borderRadius: BorderRadius.circular(24),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: Colors.white, size: 26),
            const SizedBox(width: 12),
            Text(label,
                style: const TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w800,
                  color: Colors.white,
                )),
          ],
        ),
      ),
    );
  }
}

class _Tile extends StatelessWidget {
  final String label;
  final IconData icon;
  final VoidCallback onTap;
  const _Tile({required this.label, required this.icon, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: 96,
        decoration: BoxDecoration(
          color: PosTheme.surface,
          borderRadius: BorderRadius.circular(22),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: PosTheme.text, size: 24),
            const SizedBox(height: 8),
            Text(label,
                style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: PosTheme.text)),
          ],
        ),
      ),
    );
  }
}
