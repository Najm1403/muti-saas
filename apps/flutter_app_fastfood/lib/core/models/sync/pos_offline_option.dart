import 'package:json_annotation/json_annotation.dart';

part 'pos_offline_option.g.dart';

/// A selected Variant Option stored alongside an offline sale item.
///
/// Mirrors [PosSaleVariantOptionSnapshot] but lives in the offline queue
/// model hierarchy. Display/audit snapshot only — no price (spec A1/D4).
@JsonSerializable()
class PosOfflineOption {
  /// Local DB row id; null until the row is persisted.
  final String? id;

  @JsonKey(name: 'variant_option_id')
  final String variantOptionId;

  @JsonKey(name: 'option_name')
  final String optionName;

  const PosOfflineOption({
    this.id,
    required this.variantOptionId,
    required this.optionName,
  });

  /// Constructs from the JSON within a queued offline item.
  factory PosOfflineOption.fromJson(Map<String, dynamic> json) =>
      _$PosOfflineOptionFromJson(json);

  Map<String, dynamic> toJson() => _$PosOfflineOptionToJson(this);
}
