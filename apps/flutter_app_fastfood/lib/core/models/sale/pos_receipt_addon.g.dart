// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pos_receipt_addon.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PosReceiptAddon _$PosReceiptAddonFromJson(Map<String, dynamic> json) =>
    PosReceiptAddon(
      name: json['name'] as String,
      priceDelta: json['price_delta'] as String,
      wasRemoved: json['was_removed'] as bool? ?? false,
    );

Map<String, dynamic> _$PosReceiptAddonToJson(PosReceiptAddon instance) =>
    <String, dynamic>{
      'name': instance.name,
      'price_delta': instance.priceDelta,
      'was_removed': instance.wasRemoved,
    };
