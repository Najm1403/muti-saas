import 'package:json_annotation/json_annotation.dart';
import 'pos_offline_option.dart';
import 'pos_offline_addon.dart';

part 'pos_offline_item.g.dart';

/// A sale line item stored in the local offline queue pending upload.
///
/// All monetary fields ([quantity], [unitPrice], [discount], [total]) are
/// Strings to preserve Decimal precision across the DB → JSON round-trip.
/// [variantId] is required — every cart item resolves to a real synced
/// Variant (spec F2/F3).
@JsonSerializable(explicitToJson: true)
class PosOfflineItem {
  /// Local DB row id; null until the row is persisted.
  final String? id;

  @JsonKey(name: 'variant_id')
  final String variantId;

  @JsonKey(name: 'product_id')
  final String productId;

  /// Snapshot of the product name at sale time, so receipts are correct
  /// even if the product is renamed later in the back-office.
  @JsonKey(name: 'product_name')
  final String productName;

  final String quantity;

  @JsonKey(name: 'unit_price')
  final String unitPrice;

  final String discount;
  final String total;

  final List<PosOfflineOption> options;
  final List<PosOfflineAddon> addons;

  /// Laptop Store shareable-inventory model — see PosSaleItemCreate's
  /// matching fields; carried through unchanged from the local queue row.
  @JsonKey(name: 'parent_item_id')
  final String? parentItemId;

  @JsonKey(name: 'satisfies_option_group_id')
  final String? satisfiesOptionGroupId;

  @JsonKey(name: 'component_option_id')
  final String? componentOptionId;

  const PosOfflineItem({
    this.id,
    required this.variantId,
    required this.productId,
    required this.productName,
    required this.quantity,
    required this.unitPrice,
    this.discount = '0.00',
    required this.total,
    this.options = const [],
    this.addons = const [],
    this.parentItemId,
    this.satisfiesOptionGroupId,
    this.componentOptionId,
  });

  /// Constructs from the JSON within a queued offline sale.
  factory PosOfflineItem.fromJson(Map<String, dynamic> json) =>
      _$PosOfflineItemFromJson(json);

  Map<String, dynamic> toJson() => _$PosOfflineItemToJson(this);
}
