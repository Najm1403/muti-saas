import 'package:json_annotation/json_annotation.dart';

part 'pos_sale_addon_selection.g.dart';

/// A selected (or explicitly removed) Add-on included in an online sale
/// creation request.
///
/// [priceDelta] is client-submitted but always re-verified server-side
/// against AddonItem.price_delta (spec D7) — never trusted blindly.
/// [wasRemoved] records that a `default_selected` Add-on Item was unchecked
/// by the cashier.
@JsonSerializable()
class PosSaleAddonSelection {
  /// Client-generated UUID for this row; nullable for API flexibility.
  final String? id;

  @JsonKey(name: 'addon_item_id')
  final String addonItemId;

  @JsonKey(name: 'addon_name')
  final String addonName;

  @JsonKey(name: 'price_delta')
  final String priceDelta;

  @JsonKey(name: 'was_removed')
  final bool wasRemoved;

  const PosSaleAddonSelection({
    this.id,
    required this.addonItemId,
    required this.addonName,
    this.priceDelta = '0.00',
    this.wasRemoved = false,
  });

  factory PosSaleAddonSelection.fromJson(Map<String, dynamic> json) =>
      _$PosSaleAddonSelectionFromJson(json);

  Map<String, dynamic> toJson() => _$PosSaleAddonSelectionToJson(this);
}
