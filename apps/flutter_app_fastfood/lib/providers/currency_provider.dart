import 'package:decimal/decimal.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import 'onboarding_notifier.dart';

part 'currency_provider.g.dart';

/// The shop's money display string, synced from the cloud.
///
/// Falls back to "Rs." before onboarding completes or when the cloud sends
/// nothing.
@Riverpod(keepAlive: true)
String currency(CurrencyRef ref) {
  final onboarding = ref.watch(onboardingNotifierProvider).valueOrNull;
  final c = onboarding?.currency;
  return (c == null || c.isEmpty) ? 'Rs.' : c;
}

/// Formats [amount] (a `Decimal`, `num`, or numeric `String`) as
/// `"<currency> 1,234.50"`. Use via [moneyProvider] so the prefix stays live.
String formatMoney(String currency, Object? amount) {
  double value;
  if (amount is Decimal) {
    value = amount.toDouble();
  } else if (amount is num) {
    value = amount.toDouble();
  } else {
    value = double.tryParse(amount?.toString() ?? '') ?? 0;
  }

  final negative = value < 0;
  final abs = value.abs();
  final fixed = abs.toStringAsFixed(2);
  final parts = fixed.split('.');
  final intPart = parts[0].replaceAllMapped(
    RegExp(r'\B(?=(\d{3})+(?!\d))'),
    (m) => ',',
  );
  return '${negative ? '-' : ''}$currency $intPart.${parts[1]}';
}

/// A ready-to-call money formatter bound to the current currency.
///
/// `ref.watch(moneyProvider)(item.lineTotal)` -> `"Rs. 9.00"`.
@Riverpod(keepAlive: true)
String Function(Object? amount) money(MoneyRef ref) {
  final c = ref.watch(currencyProvider);
  return (amount) => formatMoney(c, amount);
}
