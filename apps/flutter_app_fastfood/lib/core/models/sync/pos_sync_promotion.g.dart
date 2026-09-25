// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pos_sync_promotion.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PosSyncPromotion _$PosSyncPromotionFromJson(Map<String, dynamic> json) =>
    PosSyncPromotion(
      id: json['id'] as String,
      name: json['name'] as String,
      promoCode: json['promo_code'] as String?,
      type: json['type'] as String,
      discountValue: json['discount_value'] as String,
      triggerMinQty: (json['trigger_min_qty'] as num?)?.toInt(),
      triggerMinAmount: json['trigger_min_amount'] as String?,
      triggerProductId: json['trigger_product_id'] as String?,
      triggerCategoryId: json['trigger_category_id'] as String?,
      validFrom: json['valid_from'] == null
          ? null
          : DateTime.parse(json['valid_from'] as String),
      validUntil: json['valid_until'] == null
          ? null
          : DateTime.parse(json['valid_until'] as String),
      maxUses: (json['max_uses'] as num?)?.toInt(),
      usedCount: (json['used_count'] as num).toInt(),
      isActive: json['is_active'] as bool,
    );

Map<String, dynamic> _$PosSyncPromotionToJson(PosSyncPromotion instance) =>
    <String, dynamic>{
      'id': instance.id,
      'name': instance.name,
      'promo_code': instance.promoCode,
      'type': instance.type,
      'discount_value': instance.discountValue,
      'trigger_min_qty': instance.triggerMinQty,
      'trigger_min_amount': instance.triggerMinAmount,
      'trigger_product_id': instance.triggerProductId,
      'trigger_category_id': instance.triggerCategoryId,
      'valid_from': instance.validFrom?.toIso8601String(),
      'valid_until': instance.validUntil?.toIso8601String(),
      'max_uses': instance.maxUses,
      'used_count': instance.usedCount,
      'is_active': instance.isActive,
    };
