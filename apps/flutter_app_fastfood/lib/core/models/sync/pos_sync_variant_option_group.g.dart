// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pos_sync_variant_option_group.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PosSyncVariantOptionGroup _$PosSyncVariantOptionGroupFromJson(
        Map<String, dynamic> json) =>
    PosSyncVariantOptionGroup(
      id: json['id'] as String,
      productId: json['product_id'] as String,
      name: json['name'] as String,
      isRequired: json['is_required'] as bool,
      displayOrder: (json['display_order'] as num).toInt(),
      options: (json['options'] as List<dynamic>?)
              ?.map((e) =>
                  PosSyncVariantOption.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      usageType: json['usage_type'] as String? ?? 'specification',
      allowedOptionIds: (json['allowed_option_ids'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          [],
    );

Map<String, dynamic> _$PosSyncVariantOptionGroupToJson(
        PosSyncVariantOptionGroup instance) =>
    <String, dynamic>{
      'id': instance.id,
      'product_id': instance.productId,
      'name': instance.name,
      'is_required': instance.isRequired,
      'display_order': instance.displayOrder,
      'options': instance.options.map((e) => e.toJson()).toList(),
      'usage_type': instance.usageType,
      'allowed_option_ids': instance.allowedOptionIds,
    };
