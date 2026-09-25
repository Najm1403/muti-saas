// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pos_sync_addon_item.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PosSyncAddonItem _$PosSyncAddonItemFromJson(Map<String, dynamic> json) =>
    PosSyncAddonItem(
      id: json['id'] as String,
      addonGroupId: json['addon_group_id'] as String,
      name: json['name'] as String,
      priceDelta: json['price_delta'] as String,
      defaultSelected: json['default_selected'] as bool,
      displayOrder: (json['display_order'] as num).toInt(),
      isActive: json['is_active'] as bool,
    );

Map<String, dynamic> _$PosSyncAddonItemToJson(PosSyncAddonItem instance) =>
    <String, dynamic>{
      'id': instance.id,
      'addon_group_id': instance.addonGroupId,
      'name': instance.name,
      'price_delta': instance.priceDelta,
      'default_selected': instance.defaultSelected,
      'display_order': instance.displayOrder,
      'is_active': instance.isActive,
    };
