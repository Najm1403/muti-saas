// features/staff/staff_screen.dart
//
// Screen 3 — staff picker. Grid of active staff; tap -> PIN -> shift check ->
// dashboard or shift-open. Footer: New Device / Re-validate Device (admin PIN).

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/models/auth/staff_member.dart';
import '../../core/network/api_exception.dart';
import '../../providers/auth_notifier.dart';
import '../../providers/onboarding_notifier.dart';
import '../../providers/session_notifier.dart';
import '../../providers/staff_provider.dart';
import '../pos/pos_theme.dart';
import 'widgets/admin_pin_sheet.dart';
import 'widgets/pin_pad.dart';

class StaffScreen extends ConsumerWidget {
  const StaffScreen({super.key});

  Future<void> _pickStaff(
    BuildContext context,
    WidgetRef ref,
    StaffMember staff,
  ) async {
    final pin = await showPinPad(context, staffName: staff.fullName);
    if (pin == null || !context.mounted) return;

    final messenger = ScaffoldMessenger.of(context);
    try {
      await ref.read(authNotifierProvider.notifier).staffLoginWithPin(
            staff.userId,
            pin,
          );
      // Re-evaluate the shift for this cashier.
      ref.invalidate(sessionNotifierProvider);
      final session = await ref.read(sessionNotifierProvider.future);
      if (!context.mounted) return;
      context.go(session == null ? '/shift/open' : '/dashboard');
    } on ApiException catch (e) {
      messenger.showSnackBar(SnackBar(content: Text(e.message)));
    } catch (_) {
      messenger.showSnackBar(
        const SnackBar(content: Text('Could not reach the server')),
      );
    }
  }

  Future<void> _revalidate(BuildContext context, WidgetRef ref) async {
    final creds = await showAdminPinSheet(
      context,
      title: 'Deactivate this device',
      subtitle:
          'This signs the device out and returns to the activation screen.',
    );
    if (creds == null || !context.mounted) return;
    // Clears the local activation record + the device token. A fresh activation
    // code from the web dashboard is needed to pair again.
    await ref.read(onboardingNotifierProvider.notifier).resetOnboarding();
    if (context.mounted) context.go('/activate');
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final staffAsync = ref.watch(staffListProvider);
    final onboarding = ref.watch(onboardingNotifierProvider).valueOrNull;

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
                  Container(
                    width: 44,
                    height: 44,
                    decoration: const BoxDecoration(
                      color: PosTheme.accent,
                      borderRadius: PosTheme.pillRadius,
                    ),
                    padding: const EdgeInsets.all(5),
                    child: Image.asset(
                      'assets/smartshop.png',
                      fit: BoxFit.contain,
                      semanticLabel: 'Storixx',
                    ),
                  ),
                  const SizedBox(width: 14),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        onboarding?.businessName ?? 'Storixx POS',
                        style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w800,
                            color: PosTheme.text),
                      ),
                      Text(
                        onboarding?.branchName ?? '',
                        style: const TextStyle(
                            fontSize: 12, color: PosTheme.textMuted),
                      ),
                    ],
                  ),
                  const Spacer(),
                  IconButton(
                    onPressed: () => ref.invalidate(staffListProvider),
                    icon: const Icon(Icons.refresh, color: PosTheme.textMuted),
                  ),
                ],
              ),
              const SizedBox(height: 20),
              const Text(
                'WHO IS STARTING A SHIFT?',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.6,
                  color: PosTheme.accentText,
                ),
              ),
              const SizedBox(height: 14),
              Expanded(
                child: staffAsync.when(
                  loading: () => const Center(
                      child: CircularProgressIndicator(color: PosTheme.accent)),
                  error: (e, _) => Center(
                    child: Text(
                      e is ApiException ? e.message : 'Could not load staff',
                      style: const TextStyle(color: PosTheme.textMuted),
                    ),
                  ),
                  data: (staff) {
                    if (staff.isEmpty) {
                      return const Center(
                        child: Text('No active staff for this branch.',
                            style: TextStyle(color: PosTheme.textMuted)),
                      );
                    }
                    return GridView.builder(
                      gridDelegate:
                          const SliverGridDelegateWithMaxCrossAxisExtent(
                        maxCrossAxisExtent: 180,
                        crossAxisSpacing: 14,
                        mainAxisSpacing: 14,
                        childAspectRatio: 0.95,
                      ),
                      itemCount: staff.length,
                      itemBuilder: (_, i) => _StaffTile(
                        staff: staff[i],
                        onTap: () => _pickStaff(context, ref, staff[i]),
                      ),
                    );
                  },
                ),
              ),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                onPressed: () => context.push('/attendance'),
                icon: const Icon(Icons.badge_outlined, size: 18),
                style: OutlinedButton.styleFrom(
                  foregroundColor: PosTheme.text,
                  side: const BorderSide(color: PosTheme.divider, width: 2),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: const RoundedRectangleBorder(
                      borderRadius: PosTheme.pillRadius),
                ),
                label: const Text('Clock In / Out'),
              ),
              const SizedBox(height: 8),
              OutlinedButton.icon(
                onPressed: () => _revalidate(context, ref),
                icon: const Icon(Icons.tablet_android, size: 18),
                style: OutlinedButton.styleFrom(
                  foregroundColor: PosTheme.text,
                  side: const BorderSide(color: PosTheme.divider, width: 2),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: const RoundedRectangleBorder(
                      borderRadius: PosTheme.pillRadius),
                ),
                label: const Text('New device / Re-validate device'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _StaffTile extends StatelessWidget {
  final StaffMember staff;
  final VoidCallback onTap;

  const _StaffTile({required this.staff, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          color: PosTheme.surface,
          borderRadius: BorderRadius.circular(24),
        ),
        padding: const EdgeInsets.all(14),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 60,
              height: 60,
              alignment: Alignment.center,
              decoration: const BoxDecoration(
                color: PosTheme.accent2Pale,
                shape: BoxShape.circle,
              ),
              child: Text(
                staff.initials,
                style: const TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w800,
                  color: PosTheme.accent2Text,
                ),
              ),
            ),
            const SizedBox(height: 10),
            Text(
              staff.fullName,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w700,
                color: PosTheme.text,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              staff.designation,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 11, color: PosTheme.textMuted),
            ),
          ],
        ),
      ),
    );
  }
}
