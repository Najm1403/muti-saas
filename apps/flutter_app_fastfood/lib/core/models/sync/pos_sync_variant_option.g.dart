// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pos_sync_variant_option.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PosSyncVariantOption _$PosSyncVariantOptionFromJson(
        Map<String, dynamic> json) =>
    PosSyncVariantOption(
      id: json['id'] as String,
      optionGroupId: json['option_group_id'] as String,
      name: json['name'] as String,
      displayOrder: (json['display_order'] as num).toInt(),
      isActive: json['is_active'] as bool,
      componentVariantId: json['component_variant_id'] as String?,
    );

Map<String, dynamic> _$PosSyncVariantOptionToJson(
        PosSyncVariantOption instance) =>
    <String, dynamic>{
      'id': instance.id,
      'option_group_id': instance.optionGroupId,
      'name': instance.name,
      'display_order': instance.displayOrder,
      'is_active': instance.isActive,
      'component_variant_id': instance.componentVariantId,
    };
