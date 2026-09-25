// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pos_sync_variant.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PosSyncVariant _$PosSyncVariantFromJson(Map<String, dynamic> json) =>
    PosSyncVariant(
      id: json['id'] as String,
      productId: json['product_id'] as String,
      optionValueIds: (json['option_value_ids'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      salePrice: json['sale_price'] as String,
      costPrice: json['cost_price'] as String?,
      comparePrice: json['compare_price'] as String?,
      tracksInventory: json['tracks_inventory'] as bool,
      isDefault: json['is_default'] as bool,
      stockByBranch: (json['stock_by_branch'] as Map<String, dynamic>?)?.map(
        (k, e) => MapEntry(k, (e as num).toInt()),
      ),
      openingStock: (json['opening_stock'] as num?)?.toInt(),
      productName: json['product_name'] as String?,
      variantName: json['variant_name'] as String?,
      sellable: json['sellable'] as bool? ?? true,
      sellableReason: json['sellable_reason'] as String?,
      allowInventoryTracking:
          json['allow_inventory_tracking'] as bool? ?? false,
    );

Map<String, dynamic> _$PosSyncVariantToJson(PosSyncVariant instance) =>
    <String, dynamic>{
      'id': instance.id,
      'product_id': instance.productId,
      'option_value_ids': instance.optionValueIds,
      'sale_price': instance.salePrice,
      'cost_price': instance.costPrice,
      'compare_price': instance.comparePrice,
      'tracks_inventory': instance.tracksInventory,
      'is_default': instance.isDefault,
      'stock_by_branch': instance.stockByBranch,
      'opening_stock': instance.openingStock,
      'product_name': instance.productName,
      'variant_name': instance.variantName,
      'sellable': instance.sellable,
      'sellable_reason': instance.sellableReason,
      'allow_inventory_tracking': instance.allowInventoryTracking,
    };
