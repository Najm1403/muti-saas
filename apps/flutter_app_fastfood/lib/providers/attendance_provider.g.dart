// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'attendance_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$attendanceStaffListHash() =>
    r'4ebe300d102fadfda60640e6e475705a7a9f017c';

/// Active employees for this device's branch — powers the attendance grid.
/// Independent of [staffListProvider] (the cashier picker, sourced from
/// Users) — every active employee appears here.
///
/// Copied from [attendanceStaffList].
@ProviderFor(attendanceStaffList)
final attendanceStaffListProvider =
    AutoDisposeFutureProvider<List<AttendanceStaffMember>>.internal(
  attendanceStaffList,
  name: r'attendanceStaffListProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$attendanceStaffListHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef AttendanceStaffListRef
    = AutoDisposeFutureProviderRef<List<AttendanceStaffMember>>;
String _$attendanceStatusHash() => r'18fb91da2e04b0b7b86edb3011dbbae618215ee4';

/// Employees currently clocked in at this device's branch — powers the
/// "clocked in since ..." badges on the attendance grid.
///
/// Invalidate after every punch so the badge reflects the new state.
///
/// Copied from [attendanceStatus].
@ProviderFor(attendanceStatus)
final attendanceStatusProvider =
    AutoDisposeFutureProvider<List<AttendanceStatusEntry>>.internal(
  attendanceStatus,
  name: r'attendanceStatusProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$attendanceStatusHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef AttendanceStatusRef
    = AutoDisposeFutureProviderRef<List<AttendanceStatusEntry>>;
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
