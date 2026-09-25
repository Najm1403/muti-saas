// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'currency_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$currencyHash() => r'eac3dc11fdd4efb4d719159b529924f6ca474330';

/// The shop's money display string, synced from the cloud.
///
/// Falls back to "Rs." before onboarding completes or when the cloud sends
/// nothing.
///
/// Copied from [currency].
@ProviderFor(currency)
final currencyProvider = Provider<String>.internal(
  currency,
  name: r'currencyProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$currencyHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef CurrencyRef = ProviderRef<String>;
String _$moneyHash() => r'03f4e14df015727efc603a8c0b2446364db4bc97';

/// A ready-to-call money formatter bound to the current currency.
///
/// `ref.watch(moneyProvider)(item.lineTotal)` -> `"Rs. 9.00"`.
///
/// Copied from [money].
@ProviderFor(money)
final moneyProvider = Provider<String Function(Object? amount)>.internal(
  money,
  name: r'moneyProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$moneyHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef MoneyRef = ProviderRef<String Function(Object? amount)>;
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
