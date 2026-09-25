import 'package:json_annotation/json_annotation.dart';

part 'pos_receipt_payment.g.dart';

/// A payment tender as it appears on the receipt returned after a sale.
///
/// Read-only response type echoed back by the server so the receipt UI
/// can display all payment methods without additional queries.
@JsonSerializable()
class PosReceiptPayment {
  @JsonKey(name: 'payment_method')
  final String paymentMethod;

  /// Amount tendered for this method. Stored as String (Decimal).
  final String amount;

  /// Transaction or card reference, if provided at sale time.
  final String? reference;

  const PosReceiptPayment({
    required this.paymentMethod,
    required this.amount,
    this.reference,
  });

  /// Constructs from the JSON array item in [PosReceiptResponse.payments].
  factory PosReceiptPayment.fromJson(Map<String, dynamic> json) =>
      _$PosReceiptPaymentFromJson(json);

  Map<String, dynamic> toJson() => _$PosReceiptPaymentToJson(this);
}
