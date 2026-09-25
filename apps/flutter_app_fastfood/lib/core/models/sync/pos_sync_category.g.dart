// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pos_sync_category.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PosSyncCategory _$PosSyncCategoryFromJson(Map<String, dynamic> json) =>
    PosSyncCategory(
      id: json['id'] as String,
      name: json['name'] as String,
      description: json['description'] as String?,
      imagePath: json['image_path'] as String?,
      displayOrder: (json['display_order'] as num).toInt(),
      isActive: json['is_active'] as bool,
    );

Map<String, dynamic> _$PosSyncCategoryToJson(PosSyncCategory instance) =>
    <String, dynamic>{
      'id': instance.id,
      'name': instance.name,
      'description': instance.description,
      'image_path': instance.imagePath,
      'display_order': instance.displayOrder,
      'is_active': instance.isActive,
    };
