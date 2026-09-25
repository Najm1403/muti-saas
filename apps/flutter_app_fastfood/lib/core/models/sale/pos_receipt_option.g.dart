// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pos_receipt_option.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PosReceiptOption _$PosReceiptOptionFromJson(Map<String, dynamic> json) =>
    PosReceiptOption(
      optionName: json['option_name'] as String,
      priceAdjustment: json['price_adjustment'] as String,
    );

Map<String, dynamic> _$PosReceiptOptionToJson(PosReceiptOption instance) =>
    <String, dynamic>{
      'option_name': instance.optionName,
      'price_adjustment': instance.priceAdjustment,
    };
