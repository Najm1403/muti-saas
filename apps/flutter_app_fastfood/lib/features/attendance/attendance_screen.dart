// features/attendance/attendance_screen.dart
//
// Clock In / Out — reachable independent of cashier login and shift state
// (see app.dart's alwaysReachableRoutes) so an employee with a PIN but no
// pos.operate permission can still clock in/out without ever becoming a
// cashier. Reuses the same staff grid + PIN pad as the cashier staff picker.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../core/models/attendance/attendance_staff_member.dart';
import '../../core/network/api_exception.dart';
import '../../providers/attendance_provider.dart';
import '../../providers/repository_providers.dart';
import '../pos/pos_theme.dart';
import '../staff/widgets/pin_pad.dart';

class AttendanceScreen extends ConsumerWidget {
  const AttendanceScreen({super.key});

  Future<void> _punch(
    BuildContext context,
    WidgetRef ref,
    AttendanceStaffMember staff,
  ) async {
    final messenger = ScaffoldMessenger.of(context);
    if (!staff.hasPin) {
      messenger.showSnackBar(SnackBar(
        content: Text(
            '${staff.fullName} has no attendance PIN set. Ask an admin to set one from Employees.'),
      ));
      return;
    }

    final pin = await showPinPad(context, staffName: staff.fullName);
    if (pin == null || !context.mounted) return;

    try {
      final result = await ref
          .read(attendanceRepositoryProvider)
          .punch(staff.employeeId, pin);
      ref.invalidate(attendanceStatusProvider);
      if (!context.mounted) return;
      messenger.showSnackBar(SnackBar(
        content: Text(result.clockedIn
            ? '${result.fullName} clocked in at ${DateFormat('HH:mm').format(result.clockInAt.toLocal())}'
            : '${result.fullName} clocked out — '
                '${_duration(result.clockInAt, result.clockOutAt!)}'),
        backgroundColor: result.clockedIn ? Colors.green.shade700 : null,
      ));
    } on ApiException catch (e) {
      messenger.showSnackBar(SnackBar(content: Text(e.message)));
    } catch (_) {
      messenger.showSnackBar(
        const SnackBar(content: Text('Could not reach the server')),
      );
    }
  }

  static String _duration(DateTime start, DateTime end) {
    final d = end.difference(start);
    final h = d.inHours;
    final m = d.inMinutes % 60;
    return h > 0 ? '${h}h ${m}m' : '${m}m';
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final staffAsync = ref.watch(attendanceStaffListProvider);
    final statusAsync = ref.watch(attendanceStatusProvider);
    // Both sides key by employee_id now — AttendanceStaffMember is the
    // employee grid's own data source (not the User-based cashier picker),
    // and AttendanceStatusEntry.employee_id is always set.
    final clockedInSince = <String, DateTime>{
      for (final s in statusAsync.valueOrNull ?? const [])
        s.employeeId: s.clockInAt,
    };

    return Scaffold(
      backgroundColor: PosTheme.bg,
      appBar: AppBar(
        backgroundColor: PosTheme.bg,
        elevation: 0,
        foregroundColor: PosTheme.text,
        title: const Text('Clock In / Out',
            style: TextStyle(fontWeight: FontWeight.w700)),
        actions: [
          IconButton(
            onPressed: () {
              ref.invalidate(attendanceStaffListProvider);
              ref.invalidate(attendanceStatusProvider);
            },
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
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
                  child: Text('No active employees for this branch.',
                      style: TextStyle(color: PosTheme.textMuted)),
                );
              }
              return GridView.builder(
                gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
                  maxCrossAxisExtent: 180,
                  crossAxisSpacing: 14,
                  mainAxisSpacing: 14,
                  childAspectRatio: 0.9,
                ),
                itemCount: staff.length,
                itemBuilder: (_, i) => _AttendanceTile(
                  staff: staff[i],
                  clockedInSince: clockedInSince[staff[i].employeeId],
                  onTap: () => _punch(context, ref, staff[i]),
                ),
              );
            },
          ),
        ),
      ),
    );
  }
}

class _AttendanceTile extends StatelessWidget {
  final AttendanceStaffMember staff;
  final DateTime? clockedInSince;
  final VoidCallback onTap;

  const _AttendanceTile({
    required this.staff,
    required this.clockedInSince,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final clockedIn = clockedInSince != null;
    final subtitle = clockedIn
        ? 'In since ${DateFormat('HH:mm').format(clockedInSince!.toLocal())}'
        : (staff.hasPin ? (staff.designation ?? 'Staff') : 'No PIN set');
    return GestureDetector(
      onTap: onTap,
      child: Opacity(
        opacity: staff.hasPin || clockedIn ? 1 : 0.55,
        child: Container(
          decoration: BoxDecoration(
            color: PosTheme.surface,
            borderRadius: BorderRadius.circular(24),
            border: clockedIn
                ? Border.all(color: Colors.green.shade400, width: 2)
                : null,
          ),
          padding: const EdgeInsets.all(14),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 60,
                height: 60,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: clockedIn
                      ? Colors.green.shade50
                      : PosTheme.accent2Pale,
                  shape: BoxShape.circle,
                ),
                child: Text(
                  staff.initials,
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.w800,
                    color: clockedIn
                        ? Colors.green.shade700
                        : PosTheme.accent2Text,
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
                subtitle,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  fontSize: 11,
                  color: clockedIn ? Colors.green.shade700 : PosTheme.textMuted,
                  fontWeight: clockedIn ? FontWeight.w600 : FontWeight.normal,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
