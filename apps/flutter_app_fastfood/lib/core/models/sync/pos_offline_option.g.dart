// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pos_offline_option.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PosOfflineOption _$PosOfflineOptionFromJson(Map<String, dynamic> json) =>
    PosOfflineOption(
      id: json['id'] as String?,
      variantOptionId: json['variant_option_id'] as String,
      optionName: json['option_name'] as String,
    );

Map<String, dynamic> _$PosOfflineOptionToJson(PosOfflineOption instance) =>
    <String, dynamic>{
      'id': instance.id,
      'variant_option_id': instance.variantOptionId,
      'option_name': instance.optionName,
    };
