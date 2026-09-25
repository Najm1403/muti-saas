// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'cart_notifier.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$cartNotifierHash() => r'3939a790d31a669ffe1d60ce2e118916c74b8390';

/// Reactive facade over [CartService] that exposes the cart as a [CartSnapshot].
///
/// The underlying [CartService] holds mutable state; this notifier converts
/// every mutation into a new [CartSnapshot] so widgets rebuild reactively.
/// keepAlive ensures the cart survives tab or widget-tree rebuilds.
///
/// Copied from [CartNotifier].
@ProviderFor(CartNotifier)
final cartNotifierProvider =
    NotifierProvider<CartNotifier, CartSnapshot>.internal(
  CartNotifier.new,
  name: r'cartNotifierProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$cartNotifierHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

typedef _$CartNotifier = Notifier<CartSnapshot>;
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
