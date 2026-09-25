import 'package:json_annotation/json_annotation.dart';

part 'pos_sale_variant_option_snapshot.g.dart';

/// A selected Variant Option included in an online sale creation request.
///
/// Display/audit snapshot only — no price (spec A1/D4; pricing lives on
/// [PosSaleAddonSelection] instead).
@JsonSerializable()
class PosSaleVariantOptionSnapshot {
  /// Client-generated UUID for this row; nullable for API flexibility.
  final String? id;

  @JsonKey(name: 'variant_option_id')
  final String variantOptionId;

  @JsonKey(name: 'option_name')
  final String optionName;

  const PosSaleVariantOptionSnapshot({
    this.id,
    required this.variantOptionId,
    required this.optionName,
  });

  factory PosSaleVariantOptionSnapshot.fromJson(Map<String, dynamic> json) =>
      _$PosSaleVariantOptionSnapshotFromJson(json);

  Map<String, dynamic> toJson() => _$PosSaleVariantOptionSnapshotToJson(this);
}
