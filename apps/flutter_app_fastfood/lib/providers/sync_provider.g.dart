// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'sync_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$unsyncedCountHash() => r'8ac22c6980359b2a662d1426e5651cb95f409b76';

/// Live count of offline sales waiting to be uploaded.
///
/// Emits a new value whenever the [LocalSalesTable] changes, so the outbox
/// badge in the UI stays current without polling. Returns 0 when no DB exists.
///
/// Copied from [unsyncedCount].
@ProviderFor(unsyncedCount)
final unsyncedCountProvider = AutoDisposeStreamProvider<int>.internal(
  unsyncedCount,
  name: r'unsyncedCountProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$unsyncedCountHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef UnsyncedCountRef = AutoDisposeStreamProviderRef<int>;
String _$lastSyncAtHash() => r'6ca2ae1142a016cb15504e1741b9cb96f9882417';

/// Timestamp of the last successful sync from the cloud catalog.
///
/// Returns null on first launch (no sync has happened yet).
/// Used by the sync status indicator in settings or the app bar.
///
/// Copied from [lastSyncAt].
@ProviderFor(lastSyncAt)
final lastSyncAtProvider = AutoDisposeFutureProvider<DateTime?>.internal(
  lastSyncAt,
  name: r'lastSyncAtProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$lastSyncAtHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef LastSyncAtRef = AutoDisposeFutureProviderRef<DateTime?>;
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
