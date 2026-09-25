// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'repository_providers.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$authRepositoryHash() => r'8bd3ebd08e15be0bf11ec83f104f959704fc14ec';

/// Handles device activation and cashier login; persists tokens to [TokenStorage].
///
/// Copied from [authRepository].
@ProviderFor(authRepository)
final authRepositoryProvider = Provider<AuthRepository>.internal(
  authRepository,
  name: r'authRepositoryProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$authRepositoryHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef AuthRepositoryRef = ProviderRef<AuthRepository>;
String _$syncRepositoryHash() => r'93f8ac0c86faca0fd8320c433f782cca0f2480ba';

/// Orchestrates full/delta catalog sync and offline sale upload.
///
/// Copied from [syncRepository].
@ProviderFor(syncRepository)
final syncRepositoryProvider = Provider<SyncRepository>.internal(
  syncRepository,
  name: r'syncRepositoryProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$syncRepositoryHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef SyncRepositoryRef = ProviderRef<SyncRepository>;
String _$menuRepositoryHash() => r'8509e618e4effe625b8dc8dde39f5d3651c0d279';

/// Read-only access to the local catalog tables (categories, products, etc.).
///
/// Copied from [menuRepository].
@ProviderFor(menuRepository)
final menuRepositoryProvider = Provider<MenuRepository>.internal(
  menuRepository,
  name: r'menuRepositoryProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$menuRepositoryHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef MenuRepositoryRef = ProviderRef<MenuRepository>;
String _$saleRepositoryHash() => r'2d54c2e5ef085aaf09ff5d67e969031426941b21';

/// Submits sales online or queues them locally when offline.
///
/// Copied from [saleRepository].
@ProviderFor(saleRepository)
final saleRepositoryProvider = Provider<SaleRepository>.internal(
  saleRepository,
  name: r'saleRepositoryProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$saleRepositoryHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef SaleRepositoryRef = ProviderRef<SaleRepository>;
String _$sessionRepositoryHash() => r'bae0c8ffa1b94a8b0ffd58b5b22904f5a3c11598';

/// Manages cashier shift open/close/current via the session API.
///
/// Copied from [sessionRepository].
@ProviderFor(sessionRepository)
final sessionRepositoryProvider = Provider<SessionRepository>.internal(
  sessionRepository,
  name: r'sessionRepositoryProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$sessionRepositoryHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef SessionRepositoryRef = ProviderRef<SessionRepository>;
String _$attendanceRepositoryHash() =>
    r'da5eb0f276e55bf21f572a6025e0f97d7d86de88';

/// Attendance clock-in/out — device token only, no cashier session involved.
///
/// Copied from [attendanceRepository].
@ProviderFor(attendanceRepository)
final attendanceRepositoryProvider = Provider<AttendanceRepository>.internal(
  attendanceRepository,
  name: r'attendanceRepositoryProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$attendanceRepositoryHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef AttendanceRepositoryRef = ProviderRef<AttendanceRepository>;
String _$cartServiceHash() => r'e3625ec56f9d368bc7821697a18f2217b595e8bc';

/// In-memory cart — keepAlive so the cart survives widget rebuilds.
///
/// Copied from [cartService].
@ProviderFor(cartService)
final cartServiceProvider = Provider<CartService>.internal(
  cartService,
  name: r'cartServiceProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$cartServiceHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef CartServiceRef = ProviderRef<CartService>;
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
