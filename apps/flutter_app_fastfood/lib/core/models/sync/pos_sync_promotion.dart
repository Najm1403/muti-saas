import 'package:json_annotation/json_annotation.dart';

part 'pos_sync_promotion.g.dart';

/// An automatic or code-triggered discount promotion synced from the cloud.
///
/// [type] drives the discount logic (e.g. "flat", "percent", "bogo").
/// Trigger fields (min qty, min amount, product, category) are mutually
/// exclusive depending on how the promotion is configured in the back-office.
/// [usedCount] is synced for display purposes — the server enforces [maxUses].
@JsonSerializable()
class PosSyncPromotion {
  final String id;
  final String name;

  /// Optional cashier-entered code that activates this promotion.
  /// Null means the promotion is applied automatically when its trigger is met.
  @JsonKey(name: 'promo_code')
  final String? promoCode;

  /// Discount type string (e.g. "percent", "flat", "bogo").
  final String type;

  /// Discount magnitude; meaning depends on [type]. Stored as String (Decimal).
  @JsonKey(name: 'discount_value')
  final String discountValue;

  @JsonKey(name: 'trigger_min_qty')
  final int? triggerMinQty;

  @JsonKey(name: 'trigger_min_amount')
  final String? triggerMinAmount;

  @JsonKey(name: 'trigger_product_id')
  final String? triggerProductId;

  @JsonKey(name: 'trigger_category_id')
  final String? triggerCategoryId;

  @JsonKey(name: 'valid_from')
  final DateTime? validFrom;

  @JsonKey(name: 'valid_until')
  final DateTime? validUntil;

  /// Null means unlimited uses.
  @JsonKey(name: 'max_uses')
  final int? maxUses;

  @JsonKey(name: 'used_count')
  final int usedCount;

  @JsonKey(name: 'is_active')
  final bool isActive;

  const PosSyncPromotion({
    required this.id,
    required this.name,
    this.promoCode,
    required this.type,
    required this.discountValue,
    this.triggerMinQty,
    this.triggerMinAmount,
    this.triggerProductId,
    this.triggerCategoryId,
    this.validFrom,
    this.validUntil,
    this.maxUses,
    required this.usedCount,
    required this.isActive,
  });

  /// Constructs from the JSON array item in [PosSyncResponse.promotions].
  factory PosSyncPromotion.fromJson(Map<String, dynamic> json) =>
      _$PosSyncPromotionFromJson(json);

  Map<String, dynamic> toJson() => _$PosSyncPromotionToJson(this);
}
