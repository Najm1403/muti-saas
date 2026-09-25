// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pos_sale_item_create.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PosSaleItemCreate _$PosSaleItemCreateFromJson(Map<String, dynamic> json) =>
    PosSaleItemCreate(
      id: json['id'] as String?,
      variantId: json['variant_id'] as String,
      productId: json['product_id'] as String,
      productName: json['product_name'] as String,
      quantity: json['quantity'] as String,
      unitPrice: json['unit_price'] as String,
      discount: json['discount'] as String? ?? '0.00',
      total: json['total'] as String,
      options: (json['options'] as List<dynamic>?)
              ?.map((e) => PosSaleVariantOptionSnapshot.fromJson(
                  e as Map<String, dynamic>))
              .toList() ??
          const [],
      addons: (json['addons'] as List<dynamic>?)
              ?.map((e) =>
                  PosSaleAddonSelection.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      parentItemId: json['parent_item_id'] as String?,
      satisfiesOptionGroupId: json['satisfies_option_group_id'] as String?,
      componentOptionId: json['component_option_id'] as String?,
    );

Map<String, dynamic> _$PosSaleItemCreateToJson(PosSaleItemCreate instance) =>
    <String, dynamic>{
      'id': instance.id,
      'variant_id': instance.variantId,
      'product_id': instance.productId,
      'product_name': instance.productName,
      'quantity': instance.quantity,
      'unit_price': instance.unitPrice,
      'discount': instance.discount,
      'total': instance.total,
      'options': instance.options.map((e) => e.toJson()).toList(),
      'addons': instance.addons.map((e) => e.toJson()).toList(),
      'parent_item_id': instance.parentItemId,
      'satisfies_option_group_id': instance.satisfiesOptionGroupId,
      'component_option_id': instance.componentOptionId,
    };
