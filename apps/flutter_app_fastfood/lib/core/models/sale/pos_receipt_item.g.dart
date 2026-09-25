// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pos_receipt_item.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PosReceiptItem _$PosReceiptItemFromJson(Map<String, dynamic> json) =>
    PosReceiptItem(
      id: json['id'] as String?,
      parentItemId: json['parent_item_id'] as String?,
      productName: json['product_name'] as String,
      quantity: json['quantity'] as String,
      unitPrice: json['unit_price'] as String,
      discount: json['discount'] as String,
      total: json['total'] as String,
      returnedQuantity: json['returned_quantity'] as String? ?? '0',
      options: (json['options'] as List<dynamic>?)
              ?.map((e) => PosReceiptOption.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      addons: (json['addons'] as List<dynamic>?)
              ?.map((e) => PosReceiptAddon.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
    );

Map<String, dynamic> _$PosReceiptItemToJson(PosReceiptItem instance) =>
    <String, dynamic>{
      'id': instance.id,
      'parent_item_id': instance.parentItemId,
      'product_name': instance.productName,
      'quantity': instance.quantity,
      'unit_price': instance.unitPrice,
      'discount': instance.discount,
      'total': instance.total,
      'returned_quantity': instance.returnedQuantity,
      'options': instance.options.map((e) => e.toJson()).toList(),
      'addons': instance.addons.map((e) => e.toJson()).toList(),
    };
