import 'package:json_annotation/json_annotation.dart';

part 'pos_sync_addon_item.g.dart';

/// A single Add-on Item within a [PosSyncAddonGroup] (e.g. "Extra Cheese").
///
/// [priceDelta] is real pricing, always re-verified server-side at sale time
/// (spec D7) — never trusted blindly from the client.
@JsonSerializable()
class PosSyncAddonItem {
  final String id;

  @JsonKey(name: 'addon_group_id')
  final String addonGroupId;

  final String name;

  @JsonKey(name: 'price_delta')
  final String priceDelta;

  @JsonKey(name: 'default_selected')
  final bool defaultSelected;

  @JsonKey(name: 'display_order')
  final int displayOrder;

  @JsonKey(name: 'is_active')
  final bool isActive;

  const PosSyncAddonItem({
    required this.id,
    required this.addonGroupId,
    required this.name,
    required this.priceDelta,
    required this.defaultSelected,
    required this.displayOrder,
    required this.isActive,
  });

  factory PosSyncAddonItem.fromJson(Map<String, dynamic> json) =>
      _$PosSyncAddonItemFromJson(json);

  Map<String, dynamic> toJson() => _$PosSyncAddonItemToJson(this);
}
