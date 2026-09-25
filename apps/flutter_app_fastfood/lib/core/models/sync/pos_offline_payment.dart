import 'package:json_annotation/json_annotation.dart';

part 'pos_offline_payment.g.dart';

/// A payment tender recorded against an offline-queued sale.
///
/// Mirrors [PosSalePaymentCreate] in structure but belongs to the offline
/// queue model hierarchy. Split payments are supported — a single sale may
/// have multiple [PosOfflinePayment] rows (e.g. cash + card).
@JsonSerializable()
class PosOfflinePayment {
  @JsonKey(name: 'payment_method')
  final String paymentMethod;

  /// Amount tendered for this payment method. Stored as String (Decimal).
  final String amount;

  /// Optional transaction or card reference number.
  final String? reference;

  const PosOfflinePayment({
    required this.paymentMethod,
    required this.amount,
    this.reference,
  });

  /// Constructs from the JSON within a queued offline sale.
  factory PosOfflinePayment.fromJson(Map<String, dynamic> json) =>
      _$PosOfflinePaymentFromJson(json);

  Map<String, dynamic> toJson() => _$PosOfflinePaymentToJson(this);
}
