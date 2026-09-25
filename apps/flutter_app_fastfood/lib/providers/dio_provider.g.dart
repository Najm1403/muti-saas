// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'dio_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$tokenStorageHash() => r'6b9eb5c37cb6d16ea55b4e4a93b9f30eb9e0833e';

/// Singleton token storage — survives for the lifetime of the app.
///
/// device_token is read from encrypted storage; cashier_token is in-memory only.
///
/// Copied from [tokenStorage].
@ProviderFor(tokenStorage)
final tokenStorageProvider = Provider<TokenStorage>.internal(
  tokenStorage,
  name: r'tokenStorageProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$tokenStorageHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef TokenStorageRef = ProviderRef<TokenStorage>;
String _$dioHash() => r'08bd5005e0496de99ce5dd66aede10937bcd45a1';

/// Singleton Dio instance with token injection and error normalization
/// interceptors already attached. keepAlive so interceptors are not recreated.
///
/// Copied from [dio].
@ProviderFor(dio)
final dioProvider = Provider<Dio>.internal(
  dio,
  name: r'dioProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$dioHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef DioRef = ProviderRef<Dio>;
String _$deviceLockHash() => r'9c6be4ebd45e352e847c32db641bf910123b8765';

/// Holds a device lifecycle failure code, or null when the device is operating
/// normally. Set by the Dio interceptor and handled by the app shell.
///
/// Copied from [DeviceLock].
@ProviderFor(DeviceLock)
final deviceLockProvider = NotifierProvider<DeviceLock, String?>.internal(
  DeviceLock.new,
  name: r'deviceLockProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$deviceLockHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

typedef _$DeviceLock = Notifier<String?>;
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
