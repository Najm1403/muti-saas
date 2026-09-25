// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pos_offline_sale.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PosOfflineSale _$PosOfflineSaleFromJson(Map<String, dynamic> json) =>
    PosOfflineSale(
      id: json['id'] as String?,
      originProof: json['origin_proof'] as String?,
      sessionId: json['session_id'] as String?,
      saleNumber: json['sale_number'] as String,
      soldAt: DateTime.parse(json['sold_at'] as String),
      subtotal: json['subtotal'] as String,
      discount: json['discount'] as String? ?? '0.00',
      total: json['total'] as String,
      taxAmount: json['tax_amount'] as String? ?? '0.00',
      taxRate: json['tax_rate'] as String?,
      promotionId: json['promotion_id'] as String?,
      dealId: json['deal_id'] as String?,
      items: (json['items'] as List<dynamic>)
          .map((e) => PosOfflineItem.fromJson(e as Map<String, dynamic>))
          .toList(),
      payments: (json['payments'] as List<dynamic>?)
              ?.map(
                  (e) => PosOfflinePayment.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
    );

Map<String, dynamic> _$PosOfflineSaleToJson(PosOfflineSale instance) =>
    <String, dynamic>{
      'id': instance.id,
      'origin_proof': instance.originProof,
      'session_id': instance.sessionId,
      'sale_number': instance.saleNumber,
      'sold_at': instance.soldAt.toIso8601String(),
      'subtotal': instance.subtotal,
      'discount': instance.discount,
      'total': instance.total,
      'tax_amount': instance.taxAmount,
      'tax_rate': instance.taxRate,
      'promotion_id': instance.promotionId,
      'deal_id': instance.dealId,
      'items': instance.items.map((e) => e.toJson()).toList(),
      'payments': instance.payments.map((e) => e.toJson()).toList(),
    };
