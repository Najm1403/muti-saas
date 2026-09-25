import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../core/models/attendance/attendance_staff_member.dart';
import '../core/models/attendance/attendance_status_entry.dart';
import 'repository_providers.dart';

part 'attendance_provider.g.dart';

/// Active employees for this device's branch — powers the attendance grid.
/// Independent of [staffListProvider] (the cashier picker, sourced from
/// Users) — every active employee appears here.
@riverpod
Future<List<AttendanceStaffMember>> attendanceStaffList(AttendanceStaffListRef ref) =>
    ref.watch(attendanceRepositoryProvider).staff();

/// Employees currently clocked in at this device's branch — powers the
/// "clocked in since ..." badges on the attendance grid.
///
/// Invalidate after every punch so the badge reflects the new state.
@riverpod
Future<List<AttendanceStatusEntry>> attendanceStatus(AttendanceStatusRef ref) =>
    ref.watch(attendanceRepositoryProvider).status();
