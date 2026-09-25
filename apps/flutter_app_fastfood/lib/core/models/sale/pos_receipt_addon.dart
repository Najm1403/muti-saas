import 'package:json_annotation/json_annotation.dart';

part 'pos_receipt_addon.g.dart';

/// A selected (or explicitly removed) Add-on as it appears on the receipt
/// returned after a sale.
///
/// Read-only response type — the server echoes back Add-on details so the
/// receipt UI can render them without querying the local catalog.
@JsonSerializable()
class PosReceiptAddon {
  final String name;

  /// Price delta for this Add-on, as String (Decimal). "0.00" when
  /// [wasRemoved] is true.
  @JsonKey(name: 'price_delta')
  final String priceDelta;

  /// True when a `default_selected` Add-on was unchecked by the cashier
  /// (e.g. "No Onion") rather than added as an extra.
  @JsonKey(name: 'was_removed')
  final bool wasRemoved;

  const PosReceiptAddon({
    required this.name,
    required this.priceDelta,
    this.wasRemoved = false,
  });

  /// Constructs from the JSON nested within a [PosReceiptItem].
  factory PosReceiptAddon.fromJson(Map<String, dynamic> json) =>
      _$PosReceiptAddonFromJson(json);

  Map<String, dynamic> toJson() => _$PosReceiptAddonToJson(this);
}
