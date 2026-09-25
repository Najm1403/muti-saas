import 'package:json_annotation/json_annotation.dart';

part 'pos_offline_addon.g.dart';

/// A selected (or explicitly removed) Add-on stored alongside an offline
/// sale item. Mirrors [PosSaleAddonSelection] but lives in the offline queue
/// model hierarchy.
@JsonSerializable()
class PosOfflineAddon {
  /// Local DB row id; null until the row is persisted.
  final String? id;

  @JsonKey(name: 'addon_item_id')
  final String addonItemId;

  @JsonKey(name: 'addon_name')
  final String addonName;

  @JsonKey(name: 'price_delta')
  final String priceDelta;

  @JsonKey(name: 'was_removed')
  final bool wasRemoved;

  const PosOfflineAddon({
    this.id,
    required this.addonItemId,
    required this.addonName,
    this.priceDelta = '0.00',
    this.wasRemoved = false,
  });

  /// Constructs from the JSON within a queued offline item.
  factory PosOfflineAddon.fromJson(Map<String, dynamic> json) =>
      _$PosOfflineAddonFromJson(json);

  Map<String, dynamic> toJson() => _$PosOfflineAddonToJson(this);
}
