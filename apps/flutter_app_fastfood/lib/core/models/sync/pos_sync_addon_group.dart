import 'package:json_annotation/json_annotation.dart';
import 'pos_sync_addon_item.dart';

part 'pos_sync_addon_group.g.dart';

/// A shared Add-on Group (e.g. "Toppings") as attached to one product.
///
/// Structurally separate from [PosSyncVariantOptionGroup] — never feeds into
/// variant generation (spec A1/D4).
@JsonSerializable(explicitToJson: true)
class PosSyncAddonGroup {
  final String id;

  @JsonKey(name: 'product_id')
  final String productId;

  final String name;

  @JsonKey(name: 'selection_type')
  final String selectionType;

  @JsonKey(name: 'min_select')
  final int minSelect;

  @JsonKey(name: 'max_select')
  final int? maxSelect;

  @JsonKey(name: 'display_order')
  final int displayOrder;

  final List<PosSyncAddonItem> items;

  const PosSyncAddonGroup({
    required this.id,
    required this.productId,
    required this.name,
    required this.selectionType,
    required this.minSelect,
    this.maxSelect,
    required this.displayOrder,
    this.items = const [],
  });

  factory PosSyncAddonGroup.fromJson(Map<String, dynamic> json) =>
      _$PosSyncAddonGroupFromJson(json);

  Map<String, dynamic> toJson() => _$PosSyncAddonGroupToJson(this);
}
