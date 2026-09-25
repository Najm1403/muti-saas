// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pos_sale_addon_selection.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PosSaleAddonSelection _$PosSaleAddonSelectionFromJson(
        Map<String, dynamic> json) =>
    PosSaleAddonSelection(
      id: json['id'] as String?,
      addonItemId: json['addon_item_id'] as String,
      addonName: json['addon_name'] as String,
      priceDelta: json['price_delta'] as String? ?? '0.00',
      wasRemoved: json['was_removed'] as bool? ?? false,
    );

Map<String, dynamic> _$PosSaleAddonSelectionToJson(
        PosSaleAddonSelection instance) =>
    <String, dynamic>{
      'id': instance.id,
      'addon_item_id': instance.addonItemId,
      'addon_name': instance.addonName,
      'price_delta': instance.priceDelta,
      'was_removed': instance.wasRemoved,
    };
