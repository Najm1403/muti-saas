// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pos_sale_create.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PosSaleCreate _$PosSaleCreateFromJson(Map<String, dynamic> json) =>
    PosSaleCreate(
      id: json['id'] as String?,
      saleNumber: json['sale_number'] as String,
      soldAt: DateTime.parse(json['sold_at'] as String),
      subtotal: json['subtotal'] as String,
      discount: json['discount'] as String? ?? '0.00',
      total: json['total'] as String,
      taxAmount: json['tax_amount'] as String? ?? '0.00',
      taxRate: json['tax_rate'] as String?,
      promotionId: json['promotion_id'] as String?,
      dealId: json['deal_id'] as String?,
      sessionId: json['session_id'] as String?,
      items: (json['items'] as List<dynamic>)
          .map((e) => PosSaleItemCreate.fromJson(e as Map<String, dynamic>))
          .toList(),
      payments: (json['payments'] as List<dynamic>?)
              ?.map((e) =>
                  PosSalePaymentCreate.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
    );

Map<String, dynamic> _$PosSaleCreateToJson(PosSaleCreate instance) =>
    <String, dynamic>{
      'id': instance.id,
      'sale_number': instance.saleNumber,
      'sold_at': instance.soldAt.toIso8601String(),
      'subtotal': instance.subtotal,
      'discount': instance.discount,
      'total': instance.total,
      'tax_amount': instance.taxAmount,
      'tax_rate': instance.taxRate,
      'promotion_id': instance.promotionId,
      'deal_id': instance.dealId,
      'session_id': instance.sessionId,
      'items': instance.items.map((e) => e.toJson()).toList(),
      'payments': instance.payments.map((e) => e.toJson()).toList(),
    };
