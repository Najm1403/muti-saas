import 'package:json_annotation/json_annotation.dart';
import 'pos_sale_variant_option_snapshot.dart';
import 'pos_sale_addon_selection.dart';

part 'pos_sale_item_create.g.dart';

/// One line item in an online sale creation request.
///
/// All monetary fields are Strings (Decimal) to avoid floating-point precision
/// loss across serialization. [productName] is snapshotted at sale time so
/// the server receipt reflects the name shown to the customer, regardless of
/// future catalog changes. [variantId] is required — every cart item resolves
/// to a real synced Variant (spec F2/F3), never a client-side guess.
@JsonSerializable(explicitToJson: true)
class PosSaleItemCreate {
  /// Client-generated UUID for the item row; nullable for API flexibility.
  final String? id;

  @JsonKey(name: 'variant_id')
  final String variantId;

  @JsonKey(name: 'product_id')
  final String productId;

  /// Snapshot of the product name at sale time.
  @JsonKey(name: 'product_name')
  final String productName;

  final String quantity;

  @JsonKey(name: 'unit_price')
  final String unitPrice;

  final String discount;

  /// Pre-calculated line total: (unitPrice + addonsTotal) * quantity - discount.
  final String total;

  /// Display-only Variant Option selections (no price).
  final List<PosSaleVariantOptionSnapshot> options;

  /// Priced Add-on selections, may include `wasRemoved: true` entries.
  final List<PosSaleAddonSelection> addons;

  /// Laptop Store shareable-inventory model — set together only when this
  /// line is a selected 'inventory_component', tagging it back to another
  /// item's [id] in this same submission rather than nesting it — see
  /// CartItem's matching fields.
  @JsonKey(name: 'parent_item_id')
  final String? parentItemId;

  @JsonKey(name: 'satisfies_option_group_id')
  final String? satisfiesOptionGroupId;

  @JsonKey(name: 'component_option_id')
  final String? componentOptionId;

  const PosSaleItemCreate({
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

  /// Constructs from JSON (symmetric factory, required by json_serializable).
  factory PosSaleItemCreate.fromJson(Map<String, dynamic> json) =>
      _$PosSaleItemCreateFromJson(json);

  Map<String, dynamic> toJson() => _$PosSaleItemCreateToJson(this);
}
