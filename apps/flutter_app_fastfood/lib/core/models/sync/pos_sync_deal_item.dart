import 'package:json_annotation/json_annotation.dart';

part 'pos_sync_deal_item.g.dart';

/// One line within a [PosSyncDeal] specifying which product or category
/// is included and at what quantity.
///
/// Either [productId] or [categoryId] is set — never both. When [categoryId]
/// is set, any product from that category satisfies the deal slot.
/// [isFree] marks lines that are given at no charge as part of the deal.
@JsonSerializable()
class PosSyncDealItem {
  final String id;

  /// Specific product that satisfies this slot, or null if category-level.
  @JsonKey(name: 'product_id')
  final String? productId;

  /// Any product from this category satisfies the slot when [productId] is null.
  @JsonKey(name: 'category_id')
  final String? categoryId;

  final int quantity;

  @JsonKey(name: 'is_free')
  final bool isFree;

  @JsonKey(name: 'sort_order')
  final int sortOrder;

  const PosSyncDealItem({
    required this.id,
    this.productId,
    this.categoryId,
    required this.quantity,
    required this.isFree,
    required this.sortOrder,
  });

  /// Constructs from the nested JSON within [PosSyncDeal.items].
  factory PosSyncDealItem.fromJson(Map<String, dynamic> json) =>
      _$PosSyncDealItemFromJson(json);

  Map<String, dynamic> toJson() => _$PosSyncDealItemToJson(this);
}
