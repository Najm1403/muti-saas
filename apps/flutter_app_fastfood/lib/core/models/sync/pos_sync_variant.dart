import 'package:json_annotation/json_annotation.dart';

part 'pos_sync_variant.g.dart';

/// A composed, sellable SKU as received from the cloud sync endpoint —
/// mirrors schemas.variant.SyncedVariantResponse (spec D1/D2/D3).
///
/// The POS must never synthesize a variant client-side — every cart line
/// resolves to a real row synced here, matched by [productId] +
/// [optionValueIds] (spec F4). [stockByBranch] carries only this device's
/// branch when non-null (server sends the full per-branch map; the POS only
/// ever reads its own branch's entry).
@JsonSerializable()
class PosSyncVariant {
  final String id;

  @JsonKey(name: 'product_id')
  final String productId;

  @JsonKey(name: 'option_value_ids')
  final List<String> optionValueIds;

  @JsonKey(name: 'sale_price')
  final String salePrice;

  @JsonKey(name: 'cost_price')
  final String? costPrice;

  @JsonKey(name: 'compare_price')
  final String? comparePrice;

  @JsonKey(name: 'tracks_inventory')
  final bool tracksInventory;

  @JsonKey(name: 'is_default')
  final bool isDefault;

  @JsonKey(name: 'stock_by_branch')
  final Map<String, int>? stockByBranch;

  @JsonKey(name: 'opening_stock')
  final int? openingStock;

  @JsonKey(name: 'product_name')
  final String? productName;

  @JsonKey(name: 'variant_name')
  final String? variantName;

  @JsonKey(defaultValue: true)
  final bool sellable;

  /// Human-readable reason when [sellable] is false — server-computed
  /// (VariantService.compute_sellability), never guessed client-side.
  @JsonKey(name: 'sellable_reason')
  final String? sellableReason;

  @JsonKey(name: 'allow_inventory_tracking', defaultValue: false)
  final bool allowInventoryTracking;

  const PosSyncVariant({
    required this.id,
    required this.productId,
    required this.optionValueIds,
    required this.salePrice,
    this.costPrice,
    this.comparePrice,
    required this.tracksInventory,
    required this.isDefault,
    this.stockByBranch,
    this.openingStock,
    this.productName,
    this.variantName,
    this.sellable = true,
    this.sellableReason,
    this.allowInventoryTracking = false,
  });

  factory PosSyncVariant.fromJson(Map<String, dynamic> json) =>
      _$PosSyncVariantFromJson(json);

  Map<String, dynamic> toJson() => _$PosSyncVariantToJson(this);
}
