import 'package:json_annotation/json_annotation.dart';

part 'pos_sync_category.g.dart';

/// A menu category received from the cloud sync endpoint (e.g. "Burgers").
///
/// Categories are display-only on the tablet and are never modified by the POS.
@JsonSerializable()
class PosSyncCategory {
  final String id;
  final String name;
  final String? description;

  @JsonKey(name: 'image_path')
  final String? imagePath;

  @JsonKey(name: 'display_order')
  final int displayOrder;

  @JsonKey(name: 'is_active')
  final bool isActive;

  const PosSyncCategory({
    required this.id,
    required this.name,
    this.description,
    this.imagePath,
    required this.displayOrder,
    required this.isActive,
  });

  /// Constructs from the JSON array item in [PosSyncResponse.categories].
  factory PosSyncCategory.fromJson(Map<String, dynamic> json) =>
      _$PosSyncCategoryFromJson(json);

  Map<String, dynamic> toJson() => _$PosSyncCategoryToJson(this);
}
