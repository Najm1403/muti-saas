// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'session_summary.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SessionSummary _$SessionSummaryFromJson(Map<String, dynamic> json) =>
    SessionSummary(
      salesCount: (json['sales_count'] as num).toInt(),
      grossTotal: json['gross_total'] as String,
      subtotalTotal: json['subtotal_total'] as String,
      discountTotal: json['discount_total'] as String,
      taxTotal: json['tax_total'] as String,
      totalPayments: json['total_payments'] as String,
      byPaymentMethod:
          (json['by_payment_method'] as Map<String, dynamic>?)?.map(
                (k, e) => MapEntry(k, e as String),
              ) ??
              const {},
      cashSalesTotal: json['cash_sales_total'] as String,
      refundsCount: (json['refunds_count'] as num).toInt(),
      refundTotal: json['refund_total'] as String,
      refundsByPaymentMethod:
          (json['refunds_by_payment_method'] as Map<String, dynamic>?)?.map(
                (k, e) => MapEntry(k, e as String),
              ) ??
              const {},
      cancellationsCount: (json['cancellations_count'] as num?)?.toInt() ?? 0,
      cancellationTotal: json['cancellation_total'] as String? ?? '0',
      cancellationsByPaymentMethod:
          (json['cancellations_by_payment_method'] as Map<String, dynamic>?)
                  ?.map(
                (k, e) => MapEntry(k, e as String),
              ) ??
              const {},
      netTotal: json['net_total'] as String,
      openingCash: json['opening_cash'] as String,
      expectedCash: json['expected_cash'] as String,
    );

Map<String, dynamic> _$SessionSummaryToJson(SessionSummary instance) =>
    <String, dynamic>{
      'sales_count': instance.salesCount,
      'gross_total': instance.grossTotal,
      'subtotal_total': instance.subtotalTotal,
      'discount_total': instance.discountTotal,
      'tax_total': instance.taxTotal,
      'total_payments': instance.totalPayments,
      'by_payment_method': instance.byPaymentMethod,
      'cash_sales_total': instance.cashSalesTotal,
      'refunds_count': instance.refundsCount,
      'refund_total': instance.refundTotal,
      'refunds_by_payment_method': instance.refundsByPaymentMethod,
      'cancellations_count': instance.cancellationsCount,
      'cancellation_total': instance.cancellationTotal,
      'cancellations_by_payment_method': instance.cancellationsByPaymentMethod,
      'net_total': instance.netTotal,
      'opening_cash': instance.openingCash,
      'expected_cash': instance.expectedCash,
    };
