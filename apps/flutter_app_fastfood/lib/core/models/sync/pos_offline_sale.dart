import 'package:json_annotation/json_annotation.dart';
import 'pos_offline_item.dart';
import 'pos_offline_payment.dart';

part 'pos_offline_sale.g.dart';

/// A complete sale record sitting in the local offline queue awaiting upload.
///
/// Built from [LocalSalesTable] rows and their related items/payments when
/// assembling a [PosUploadRequest]. [saleNumber] is unique and generated
/// client-side so duplicates can be detected server-side on upload.
@JsonSerializable(explicitToJson: true)
class PosOfflineSale {
  /// Client-generated UUID; null until first persisted to the local DB.
  final String? id;
  @JsonKey(name: 'origin_proof')
  final String? originProof;
  @JsonKey(name: 'session_id')
  final String? sessionId;

  @JsonKey(name: 'sale_number')
  final String saleNumber;

  /// UTC timestamp of when the cashier finalized the sale.
  @JsonKey(name: 'sold_at')
  final DateTime soldAt;

  /// Pre-discount, pre-tax sum of all line totals. Stored as String (Decimal).
  final String subtotal;
  final String discount;
  final String total;

  @JsonKey(name: 'tax_amount')
  final String taxAmount;

  /// The tax rate string (e.g. "0.15") applied, or null if no tax was used.
  @JsonKey(name: 'tax_rate')
  final String? taxRate;

  @JsonKey(name: 'promotion_id')
  final String? promotionId;

  @JsonKey(name: 'deal_id')
  final String? dealId;

  final List<PosOfflineItem> items;
  final List<PosOfflinePayment> payments;

  const PosOfflineSale({
    this.id,
    this.originProof,
    this.sessionId,
    required this.saleNumber,
    required this.soldAt,
    required this.subtotal,
    this.discount = '0.00',
    required this.total,
    this.taxAmount = '0.00',
    this.taxRate,
    this.promotionId,
    this.dealId,
    required this.items,
    this.payments = const [],
  });

  /// Constructs from the JSON within a [PosUploadRequest].
  factory PosOfflineSale.fromJson(Map<String, dynamic> json) =>
      _$PosOfflineSaleFromJson(json);

  Map<String, dynamic> toJson() => _$PosOfflineSaleToJson(this);
}
