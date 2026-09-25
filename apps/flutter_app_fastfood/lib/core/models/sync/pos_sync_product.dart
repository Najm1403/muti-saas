import 'package:json_annotation/json_annotation.dart';
import 'pos_sync_variant_option_group.dart';
import 'pos_sync_addon_group.dart';

part 'pos_sync_product.g.dart';

/// A menu product as received from the cloud sync endpoint.
///
/// Products are read-only on the tablet — the POS never creates or modifies
/// catalog data. [price] seeds the default variant's sale price (spec D1) —
/// there is no base_price any more. [variantOptionGroups] and [addonGroups]
/// are two structurally separate trees (spec A1/D4) synced inline to avoid
/// extra round-trips.
@JsonSerializable(explicitToJson: true)
class PosSyncProduct {
  final String id;

  @JsonKey(name: 'category_id')
  final String categoryId;

  @JsonKey(name: 'product_code')
  final String productCode;

  final String name;
  final String? description;

  /// Default (zero-option) variant's sale price. Stored as String (Decimal).
  final String price;

  @JsonKey(name: 'image_path')
  final String? imagePath;

  @JsonKey(name: 'display_order')
  final int displayOrder;

  @JsonKey(name: 'is_active')
  final bool isActive;

  @JsonKey(name: 'default_variant_id')
  final String? defaultVariantId;

  /// Single-select, SKU-defining groups (spec A1) — never priced.
  @JsonKey(name: 'variant_option_groups')
  final List<PosSyncVariantOptionGroup> variantOptionGroups;

  /// Multi-select, priced groups (spec A1) — never generates a SKU.
  @JsonKey(name: 'addon_groups')
  final List<PosSyncAddonGroup> addonGroups;

  /// Master inventory switch for the product. Variant rows still decide which
  /// composed SKUs are tracked.
  @JsonKey(name: 'allow_inventory_tracking', defaultValue: false)
  final bool allowInventoryTracking;

  const PosSyncProduct({
    required this.id,
    required this.categoryId,
    required this.productCode,
    required this.name,
    this.description,
    required this.price,
    this.imagePath,
    required this.displayOrder,
    required this.isActive,
    this.defaultVariantId,
    this.variantOptionGroups = const [],
    this.addonGroups = const [],
    this.allowInventoryTracking = false,
  });

  /// Constructs from the JSON array item in [PosSyncResponse.products].
  factory PosSyncProduct.fromJson(Map<String, dynamic> json) =>
      _$PosSyncProductFromJson(json);

  /// [explicitToJson] ensures nested lists are fully serialized.
  Map<String, dynamic> toJson() => _$PosSyncProductToJson(this);
}
