// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pos_sync_addon_group.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PosSyncAddonGroup _$PosSyncAddonGroupFromJson(Map<String, dynamic> json) =>
    PosSyncAddonGroup(
      id: json['id'] as String,
      productId: json['product_id'] as String,
      name: json['name'] as String,
      selectionType: json['selection_type'] as String,
      minSelect: (json['min_select'] as num).toInt(),
      maxSelect: (json['max_select'] as num?)?.toInt(),
      displayOrder: (json['display_order'] as num).toInt(),
      items: (json['items'] as List<dynamic>?)
              ?.map((e) => PosSyncAddonItem.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
    );

Map<String, dynamic> _$PosSyncAddonGroupToJson(PosSyncAddonGroup instance) =>
    <String, dynamic>{
      'id': instance.id,
      'product_id': instance.productId,
      'name': instance.name,
      'selection_type': instance.selectionType,
      'min_select': instance.minSelect,
      'max_select': instance.maxSelect,
      'display_order': instance.displayOrder,
      'items': instance.items.map((e) => e.toJson()).toList(),
    };
