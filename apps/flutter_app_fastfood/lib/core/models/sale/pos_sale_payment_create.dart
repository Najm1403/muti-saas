import 'package:json_annotation/json_annotation.dart';

part 'pos_sale_payment_create.g.dart';

/// A single payment tender included in an online sale creation request.
///
/// Split payments are supported — a [PosSaleCreate] may contain multiple
/// instances with different [paymentMethod] values (e.g. cash + card).
@JsonSerializable()
class PosSalePaymentCreate {
  @JsonKey(name: 'payment_method')
  final String paymentMethod;

  /// Amount tendered for this payment method. Stored as String (Decimal).
  final String amount;

  /// Optional transaction or card authorization reference.
  final String? reference;

  const PosSalePaymentCreate({
    required this.paymentMethod,
    required this.amount,
    this.reference,
  });

  factory PosSalePaymentCreate.fromJson(Map<String, dynamic> json) =>
      _$PosSalePaymentCreateFromJson(json);

  Map<String, dynamic> toJson() => _$PosSalePaymentCreateToJson(this);
}
