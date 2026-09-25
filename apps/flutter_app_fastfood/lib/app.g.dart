// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'app.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$routerHash() => r'ba920df779255522744545f029b3fb259aead39a';

/// Application router with activation + shift gate redirects.
///
/// Redirect chain on every navigation:
///   1. Not activated (no branch context)  → /activate
///   2. Activated, no staff signed in       → /staff
///   3. Staff signed in, no open shift      → /shift/open
///   4. Staff signed in, open shift         → /dashboard  (/pos reachable)
///
/// [refreshListenable] bumps whenever activation / auth / session state
/// changes so redirects re-run automatically.
///
/// Copied from [router].
@ProviderFor(router)
final routerProvider = Provider<GoRouter>.internal(
  router,
  name: r'routerProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$routerHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef RouterRef = ProviderRef<GoRouter>;
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
