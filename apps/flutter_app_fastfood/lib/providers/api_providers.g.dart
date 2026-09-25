// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'api_providers.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$posAuthApiHash() => r'685cafacbbc6fc961a2bac7cbfe8d1ecba07e3ce';

/// Thin HTTP client for device activation and cashier login.
///
/// Copied from [posAuthApi].
@ProviderFor(posAuthApi)
final posAuthApiProvider = Provider<PosAuthApi>.internal(
  posAuthApi,
  name: r'posAuthApiProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$posAuthApiHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef PosAuthApiRef = ProviderRef<PosAuthApi>;
String _$posSyncApiHash() => r'd7f4edca878ea1d9e5d433a1ddc5fff4aed0d41a';

/// Thin HTTP client for full/delta sync and offline sale upload.
///
/// Copied from [posSyncApi].
@ProviderFor(posSyncApi)
final posSyncApiProvider = Provider<PosSyncApi>.internal(
  posSyncApi,
  name: r'posSyncApiProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$posSyncApiHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef PosSyncApiRef = ProviderRef<PosSyncApi>;
String _$posSaleApiHash() => r'1071fb5b9260d5d095814a91744412541e3d3b68';

/// Thin HTTP client for online sale creation and receipt fetch.
///
/// Copied from [posSaleApi].
@ProviderFor(posSaleApi)
final posSaleApiProvider = Provider<PosSaleApi>.internal(
  posSaleApi,
  name: r'posSaleApiProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$posSaleApiHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef PosSaleApiRef = ProviderRef<PosSaleApi>;
String _$posSessionApiHash() => r'32dd4a3c94cebb79dc6c27d7a7d076702bcedc61';

/// Thin HTTP client for cashier session open/close/current.
///
/// Copied from [posSessionApi].
@ProviderFor(posSessionApi)
final posSessionApiProvider = Provider<PosSessionApi>.internal(
  posSessionApi,
  name: r'posSessionApiProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$posSessionApiHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef PosSessionApiRef = ProviderRef<PosSessionApi>;
String _$posDeviceApiHash() => r'8e93a408a685c1ac3ec8b805b492fc5d56da1200';

/// Thin HTTP client for the device heartbeat endpoint.
///
/// Copied from [posDeviceApi].
@ProviderFor(posDeviceApi)
final posDeviceApiProvider = Provider<PosDeviceApi>.internal(
  posDeviceApi,
  name: r'posDeviceApiProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$posDeviceApiHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef PosDeviceApiRef = ProviderRef<PosDeviceApi>;
String _$posAttendanceApiHash() => r'0ddc4ed074809a3ed812675b4dda0c84be2b0c62';

/// Thin HTTP client for attendance clock-in/out (device token only).
///
/// Copied from [posAttendanceApi].
@ProviderFor(posAttendanceApi)
final posAttendanceApiProvider = Provider<PosAttendanceApi>.internal(
  posAttendanceApi,
  name: r'posAttendanceApiProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$posAttendanceApiHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef PosAttendanceApiRef = ProviderRef<PosAttendanceApi>;
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
