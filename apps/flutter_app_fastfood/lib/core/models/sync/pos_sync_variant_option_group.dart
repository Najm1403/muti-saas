import 'package:json_annotation/json_annotation.dart';
import 'pos_sync_variant_option.dart';

part 'pos_sync_variant_option_group.g.dart';

/// A shared Variant Option Group (e.g. "Size") as attached to one product.
///
/// Always single-select — there is no min/max_selections here (spec A1),
/// only the per-product [isRequired] override.
@JsonSerializable(explicitToJson: true)
class PosSyncVariantOptionGroup {
  final String id;

  @JsonKey(name: 'product_id')
  final String productId;

  final String name;

  @JsonKey(name: 'is_required')
  final bool isRequired;

  @JsonKey(name: 'display_order')
  final int displayOrder;

  final List<PosSyncVariantOption> options;

  /// Laptop Store shareable-inventory model — 'specification' (default):
  /// unchanged today's behavior, options define a combination Variant.
  /// 'inventory_component': the POS must offer [options] as a dynamic,
  /// independently priced/stocked pick at sale time instead.
  @JsonKey(name: 'usage_type', defaultValue: 'specification')
  final String usageType;

  /// Which of [options] apply to this product (spec §22) — empty means
  /// every option above is offered.
  @JsonKey(name: 'allowed_option_ids', defaultValue: [])
  final List<String> allowedOptionIds;

  const PosSyncVariantOptionGroup({
    required this.id,
    required this.productId,
    required this.name,
    required this.isRequired,
    required this.displayOrder,
    this.options = const [],
    this.usageType = 'specification',
    this.allowedOptionIds = const [],
  });

  factory PosSyncVariantOptionGroup.fromJson(Map<String, dynamic> json) =>
      _$PosSyncVariantOptionGroupFromJson(json);

  Map<String, dynamic> toJson() => _$PosSyncVariantOptionGroupToJson(this);
}
