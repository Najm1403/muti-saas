import 'package:json_annotation/json_annotation.dart';

part 'session_summary.g.dart';

/// End-of-shift reconciliation figures for one cashier session.
///
/// All money values are Decimal-safe strings. [byPaymentMethod] maps a method
/// name ("CASH", "CARD", …) to its total for the shift.
@JsonSerializable()
class SessionSummary {
  @JsonKey(name: 'sales_count')
  final int salesCount;

  @JsonKey(name: 'gross_total')
  final String grossTotal;

  @JsonKey(name: 'subtotal_total')
  final String subtotalTotal;

  @JsonKey(name: 'discount_total')
  final String discountTotal;

  @JsonKey(name: 'tax_total')
  final String taxTotal;

  @JsonKey(name: 'total_payments')
  final String totalPayments;

  @JsonKey(name: 'by_payment_method')
  final Map<String, String> byPaymentMethod;

  @JsonKey(name: 'cash_sales_total')
  final String cashSalesTotal;

  @JsonKey(name: 'refunds_count')
  final int refundsCount;

  @JsonKey(name: 'refund_total')
  final String refundTotal;

  @JsonKey(name: 'refunds_by_payment_method')
  final Map<String, String> refundsByPaymentMethod;

  @JsonKey(name: 'cancellations_count', defaultValue: 0)
  final int cancellationsCount;

  @JsonKey(name: 'cancellation_total', defaultValue: '0')
  final String cancellationTotal;

  @JsonKey(name: 'cancellations_by_payment_method')
  final Map<String, String> cancellationsByPaymentMethod;

  @JsonKey(name: 'net_total')
  final String netTotal;

  @JsonKey(name: 'opening_cash')
  final String openingCash;

  @JsonKey(name: 'expected_cash')
  final String expectedCash;

  const SessionSummary({
    required this.salesCount,
    required this.grossTotal,
    required this.subtotalTotal,
    required this.discountTotal,
    required this.taxTotal,
    required this.totalPayments,
    this.byPaymentMethod = const {},
    required this.cashSalesTotal,
    required this.refundsCount,
    required this.refundTotal,
    this.refundsByPaymentMethod = const {},
    this.cancellationsCount = 0,
    this.cancellationTotal = '0',
    this.cancellationsByPaymentMethod = const {},
    required this.netTotal,
    required this.openingCash,
    required this.expectedCash,
  });

  factory SessionSummary.fromJson(Map<String, dynamic> json) =>
      _$SessionSummaryFromJson(json);

  Map<String, dynamic> toJson() => _$SessionSummaryToJson(this);
}
