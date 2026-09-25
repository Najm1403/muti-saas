import 'package:json_annotation/json_annotation.dart';
import 'pos_sync_deal_item.dart';

part 'pos_sync_deal.g.dart';

/// A bundled deal (e.g. "Meal Deal #1") synced from the cloud.
///
/// A deal can be priced either as a [fixedPrice] for the entire bundle or
/// as a [discountValue] applied as a flat amount or percentage according
/// to [discountType]. [validFrom]/[validUntil] are enforced by the UI
/// to hide expired deals from cashiers.
@JsonSerializable(explicitToJson: true)
class PosSyncDeal {
  final String id;
  final String name;
  final String? description;

  @JsonKey(name: 'deal_code')
  final String dealCode;

  /// Fixed bundle price (String Decimal). Null when discount-based pricing is used.
  @JsonKey(name: 'fixed_price')
  final String? fixedPrice;

  /// Discount amount or percentage; interpreted alongside [discountType].
  @JsonKey(name: 'discount_value')
  final String? discountValue;

  /// "flat" or "percent" — describes how [discountValue] is applied.
  @JsonKey(name: 'discount_type')
  final String? discountType;

  @JsonKey(name: 'valid_from')
  final DateTime? validFrom;

  @JsonKey(name: 'valid_until')
  final DateTime? validUntil;

  @JsonKey(name: 'is_active')
  final bool isActive;

  /// The required product/category slots that make up this deal.
  final List<PosSyncDealItem> items;

  const PosSyncDeal({
    required this.id,
    required this.name,
    this.description,
    required this.dealCode,
    this.fixedPrice,
    this.discountValue,
    this.discountType,
    this.validFrom,
    this.validUntil,
    required this.isActive,
    this.items = const [],
  });

  /// Constructs from the JSON array item in [PosSyncResponse.deals].
  factory PosSyncDeal.fromJson(Map<String, dynamic> json) =>
      _$PosSyncDealFromJson(json);

  /// [explicitToJson] ensures nested [items] are fully serialized.
  Map<String, dynamic> toJson() => _$PosSyncDealToJson(this);
}
