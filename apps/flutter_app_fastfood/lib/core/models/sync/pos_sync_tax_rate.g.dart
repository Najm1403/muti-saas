// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pos_sync_tax_rate.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PosSyncTaxRate _$PosSyncTaxRateFromJson(Map<String, dynamic> json) =>
    PosSyncTaxRate(
      id: json['id'] as String,
      name: json['name'] as String,
      rate: json['rate'] as String,
      isInclusive: json['is_inclusive'] as bool,
      isDefault: json['is_default'] as bool,
    );

Map<String, dynamic> _$PosSyncTaxRateToJson(PosSyncTaxRate instance) =>
    <String, dynamic>{
      'id': instance.id,
      'name': instance.name,
      'rate': instance.rate,
      'is_inclusive': instance.isInclusive,
      'is_default': instance.isDefault,
    };
