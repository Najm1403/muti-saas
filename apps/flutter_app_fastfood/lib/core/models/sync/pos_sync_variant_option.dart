import 'package:json_annotation/json_annotation.dart';

part 'pos_sync_variant_option.g.dart';

/// A single selectable Variant Option within a [PosSyncVariantOptionGroup]
/// (e.g. "Large"). No price here — Variant Options only ever define the SKU
/// (spec A1/D4); price deltas belong to Add-on Items instead.
@JsonSerializable()
class PosSyncVariantOption {
  final String id;

  @JsonKey(name: 'option_group_id')
  final String optionGroupId;

  final String name;

  @JsonKey(name: 'display_order')
  final int displayOrder;

  @JsonKey(name: 'is_active')
  final bool isActive;

  /// Laptop Store shareable-inventory model — set only when this option is
  /// tracked as a shared inventory component. Resolves this option's own
  /// price/stock via the already-synced Variants list — no separate data
  /// source needed.
  @JsonKey(name: 'component_variant_id')
  final String? componentVariantId;

  const PosSyncVariantOption({
    required this.id,
    required this.optionGroupId,
    required this.name,
    required this.displayOrder,
    required this.isActive,
    this.componentVariantId,
  });

  factory PosSyncVariantOption.fromJson(Map<String, dynamic> json) =>
      _$PosSyncVariantOptionFromJson(json);

  Map<String, dynamic> toJson() => _$PosSyncVariantOptionToJson(this);
}
