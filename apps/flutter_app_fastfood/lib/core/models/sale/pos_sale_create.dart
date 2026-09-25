import 'package:json_annotation/json_annotation.dart';
import 'pos_sale_item_create.dart';
import 'pos_sale_payment_create.dart';

part 'pos_sale_create.g.dart';

/// Full sale payload sent to POST /sales when the device is online.
///
/// The client generates [id] (UUID v4) and [saleNumber] before the request so
/// the server can deduplicate if the same sale is submitted more than once
/// (e.g. after a network timeout retry). All monetary fields are Strings
/// (Decimal) to avoid floating-point precision loss across serialization.
@JsonSerializable(explicitToJson: true)
class PosSaleCreate {
  /// Client-generated UUID preserved on the server as the sale's primary key.
  final String? id;

  @JsonKey(name: 'sale_number')
  final String saleNumber;

  /// UTC timestamp recorded when the cashier confirmed the sale.
  @JsonKey(name: 'sold_at')
  final DateTime soldAt;

  final String subtotal;
  final String discount;
  final String total;

  @JsonKey(name: 'tax_amount')
  final String taxAmount;

  /// Decimal rate string (e.g. "0.15"), or null when no tax applies.
  @JsonKey(name: 'tax_rate')
  final String? taxRate;

  @JsonKey(name: 'promotion_id')
  final String? promotionId;

  @JsonKey(name: 'deal_id')
  final String? dealId;

  /// Open cashier shift that owns this sale. The server validates that it
  /// belongs to the authenticated cashier, branch, and device.
  @JsonKey(name: 'session_id')
  final String? sessionId;

  final List<PosSaleItemCreate> items;
  final List<PosSalePaymentCreate> payments;

  const PosSaleCreate({
    this.id,
    required this.saleNumber,
    required this.soldAt,
    required this.subtotal,
    this.discount = '0.00',
    required this.total,
    this.taxAmount = '0.00',
    this.taxRate,
    this.promotionId,
    this.dealId,
    this.sessionId,
    required this.items,
    this.payments = const [],
  });

  factory PosSaleCreate.fromJson(Map<String, dynamic> json) =>
      _$PosSaleCreateFromJson(json);

  Map<String, dynamic> toJson() => _$PosSaleCreateToJson(this);
}
