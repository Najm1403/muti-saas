// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pos_sync_deal.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PosSyncDeal _$PosSyncDealFromJson(Map<String, dynamic> json) => PosSyncDeal(
      id: json['id'] as String,
      name: json['name'] as String,
      description: json['description'] as String?,
      dealCode: json['deal_code'] as String,
      fixedPrice: json['fixed_price'] as String?,
      discountValue: json['discount_value'] as String?,
      discountType: json['discount_type'] as String?,
      validFrom: json['valid_from'] == null
          ? null
          : DateTime.parse(json['valid_from'] as String),
      validUntil: json['valid_until'] == null
          ? null
          : DateTime.parse(json['valid_until'] as String),
      isActive: json['is_active'] as bool,
      items: (json['items'] as List<dynamic>?)
              ?.map((e) => PosSyncDealItem.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
    );

Map<String, dynamic> _$PosSyncDealToJson(PosSyncDeal instance) =>
    <String, dynamic>{
      'id': instance.id,
      'name': instance.name,
      'description': instance.description,
      'deal_code': instance.dealCode,
      'fixed_price': instance.fixedPrice,
      'discount_value': instance.discountValue,
      'discount_type': instance.discountType,
      'valid_from': instance.validFrom?.toIso8601String(),
      'valid_until': instance.validUntil?.toIso8601String(),
      'is_active': instance.isActive,
      'items': instance.items.map((e) => e.toJson()).toList(),
    };
