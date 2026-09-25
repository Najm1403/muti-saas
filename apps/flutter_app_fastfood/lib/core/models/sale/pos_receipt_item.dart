import 'package:json_annotation/json_annotation.dart';
import 'pos_receipt_addon.dart';
import 'pos_receipt_option.dart';

part 'pos_receipt_item.g.dart';

/// A single line item as it appears on the receipt returned after a sale.
///
/// All monetary fields are Strings (Decimal). This is a read-only response
/// type — it is never sent to the server, only received from it.
@JsonSerializable(explicitToJson: true)
class PosReceiptItem {
  final String? id;

  /// Laptop Store shareable-inventory model — set when this line is a
  /// selected Inventory Component (e.g. a RAM stick), pointing back to the
  /// [id] of the base line it was selected for. Used only to group/indent
  /// receipt display; never affects pricing.
  @JsonKey(name: 'parent_item_id')
  final String? parentItemId;

  @JsonKey(name: 'product_name')
  final String productName;

  final String quantity;

  @JsonKey(name: 'unit_price')
  final String unitPrice;

  final String discount;

  /// Pre-calculated line total as confirmed by the server.
  final String total;

  @JsonKey(name: 'returned_quantity', defaultValue: '0')
  final String returnedQuantity;

  final List<PosReceiptOption> options;

  final List<PosReceiptAddon> addons;

  const PosReceiptItem({
    this.id,
    this.parentItemId,
    required this.productName,
    required this.quantity,
    required this.unitPrice,
    required this.discount,
    required this.total,
    this.returnedQuantity = '0',
    this.options = const [],
    this.addons = const [],
  });

  /// Constructs from the JSON array item in [PosReceiptResponse.items].
  factory PosReceiptItem.fromJson(Map<String, dynamic> json) =>
      _$PosReceiptItemFromJson(json);

  Map<String, dynamic> toJson() => _$PosReceiptItemToJson(this);
}

/// Reorders [items] so each Inventory Component line (see
/// [PosReceiptItem.parentItemId]) is placed directly after the base line it
/// was selected for — regardless of the order the server returned them in.
/// A component whose parent isn't present in this receipt is still shown,
/// at the end, rather than silently dropped. Shared by both the on-screen
/// receipt preview and the printed/PDF receipt template.
List<PosReceiptItem> groupReceiptItemsForDisplay(List<PosReceiptItem> items) {
  final byParent = <String, List<PosReceiptItem>>{};
  final orphans = <PosReceiptItem>[];
  for (final item in items) {
    final parentId = item.parentItemId;
    if (parentId == null) continue;
    if (items.any((i) => i.id == parentId)) {
      byParent.putIfAbsent(parentId, () => []).add(item);
    } else {
      orphans.add(item);
    }
  }
  final ordered = <PosReceiptItem>[];
  for (final item in items) {
    if (item.parentItemId != null) continue;
    ordered.add(item);
    if (item.id != null) ordered.addAll(byParent[item.id] ?? const []);
  }
  ordered.addAll(orphans);
  return ordered;
}
