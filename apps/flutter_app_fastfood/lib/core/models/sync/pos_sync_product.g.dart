// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pos_sync_product.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PosSyncProduct _$PosSyncProductFromJson(Map<String, dynamic> json) =>
    PosSyncProduct(
      id: json['id'] as String,
      categoryId: json['category_id'] as String,
      productCode: json['product_code'] as String,
      name: json['name'] as String,
      description: json['description'] as String?,
      price: json['price'] as String,
      imagePath: json['image_path'] as String?,
      displayOrder: (json['display_order'] as num).toInt(),
      isActive: json['is_active'] as bool,
      defaultVariantId: json['default_variant_id'] as String?,
      variantOptionGroups: (json['variant_option_groups'] as List<dynamic>?)
              ?.map((e) =>
                  PosSyncVariantOptionGroup.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      addonGroups: (json['addon_groups'] as List<dynamic>?)
              ?.map(
                  (e) => PosSyncAddonGroup.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      allowInventoryTracking:
          json['allow_inventory_tracking'] as bool? ?? false,
    );

Map<String, dynamic> _$PosSyncProductToJson(PosSyncProduct instance) =>
    <String, dynamic>{
      'id': instance.id,
      'category_id': instance.categoryId,
      'product_code': instance.productCode,
      'name': instance.name,
      'description': instance.description,
      'price': instance.price,
      'image_path': instance.imagePath,
      'display_order': instance.displayOrder,
      'is_active': instance.isActive,
      'default_variant_id': instance.defaultVariantId,
      'variant_option_groups':
          instance.variantOptionGroups.map((e) => e.toJson()).toList(),
      'addon_groups': instance.addonGroups.map((e) => e.toJson()).toList(),
      'allow_inventory_tracking': instance.allowInventoryTracking,
    };
