// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'session_notifier.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$sessionNotifierHash() => r'f9a4f61396585a42c6da293b524818c58edd08e0';

/// Manages the cashier shift session for the lifetime of the app.
///
/// [build] fetches the current open session from the server whenever a cashier
/// is logged in. Returns null when no session is open (prompts the router to
/// redirect to /session/open). Session data is online-only — the server is
/// authoritative for opening/closing times and cash reconciliation.
///
/// Copied from [SessionNotifier].
@ProviderFor(SessionNotifier)
final sessionNotifierProvider =
    AsyncNotifierProvider<SessionNotifier, SessionResponse?>.internal(
  SessionNotifier.new,
  name: r'sessionNotifierProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$sessionNotifierHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

typedef _$SessionNotifier = AsyncNotifier<SessionResponse?>;
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
