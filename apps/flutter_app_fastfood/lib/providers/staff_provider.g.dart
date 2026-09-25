// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'staff_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$staffListHash() => r'03eebf20ba89dac4c46caef0b2f31ed0c1c4a231';

/// Active staff for this device's branch — powers the staff-picker grid.
///
/// Requires a device token (onboarding complete). Invalidate to refresh after
/// a sync or when returning to the staff screen.
///
/// Copied from [staffList].
@ProviderFor(staffList)
final staffListProvider = AutoDisposeFutureProvider<List<StaffMember>>.internal(
  staffList,
  name: r'staffListProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$staffListHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef StaffListRef = AutoDisposeFutureProviderRef<List<StaffMember>>;
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
