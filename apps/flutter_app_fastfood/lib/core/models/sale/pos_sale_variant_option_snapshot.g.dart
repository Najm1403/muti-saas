// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pos_sale_variant_option_snapshot.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PosSaleVariantOptionSnapshot _$PosSaleVariantOptionSnapshotFromJson(
        Map<String, dynamic> json) =>
    PosSaleVariantOptionSnapshot(
      id: json['id'] as String?,
      variantOptionId: json['variant_option_id'] as String,
      optionName: json['option_name'] as String,
    );

Map<String, dynamic> _$PosSaleVariantOptionSnapshotToJson(
        PosSaleVariantOptionSnapshot instance) =>
    <String, dynamic>{
      'id': instance.id,
      'variant_option_id': instance.variantOptionId,
      'option_name': instance.optionName,
    };
