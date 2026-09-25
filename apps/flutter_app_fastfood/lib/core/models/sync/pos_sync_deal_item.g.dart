// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pos_sync_deal_item.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PosSyncDealItem _$PosSyncDealItemFromJson(Map<String, dynamic> json) =>
    PosSyncDealItem(
      id: json['id'] as String,
      productId: json['product_id'] as String?,
      categoryId: json['category_id'] as String?,
      quantity: (json['quantity'] as num).toInt(),
      isFree: json['is_free'] as bool,
      sortOrder: (json['sort_order'] as num).toInt(),
    );

Map<String, dynamic> _$PosSyncDealItemToJson(PosSyncDealItem instance) =>
    <String, dynamic>{
      'id': instance.id,
      'product_id': instance.productId,
      'category_id': instance.categoryId,
      'quantity': instance.quantity,
      'is_free': instance.isFree,
      'sort_order': instance.sortOrder,
    };
