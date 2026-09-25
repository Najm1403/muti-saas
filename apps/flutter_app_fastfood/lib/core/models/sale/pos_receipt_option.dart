import 'package:json_annotation/json_annotation.dart';

part 'pos_receipt_option.g.dart';

/// A selected option as it appears on a printed or displayed receipt.
///
/// Read-only response type — the server echoes back option details so the
/// receipt UI can render them without querying the local catalog.
@JsonSerializable()
class PosReceiptOption {
  @JsonKey(name: 'option_name')
  final String optionName;

  /// Price delta for this option, as String (Decimal). May be "0.00".
  @JsonKey(name: 'price_adjustment')
  final String priceAdjustment;

  const PosReceiptOption({
    required this.optionName,
    required this.priceAdjustment,
  });

  /// Constructs from the JSON nested within a [PosReceiptItem].
  factory PosReceiptOption.fromJson(Map<String, dynamic> json) =>
      _$PosReceiptOptionFromJson(json);

  Map<String, dynamic> toJson() => _$PosReceiptOptionToJson(this);
}
