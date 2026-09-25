import 'package:json_annotation/json_annotation.dart';
import 'pos_receipt_item.dart';
import 'pos_receipt_payment.dart';

part 'pos_receipt_response.g.dart';

/// Full receipt payload returned by the server after a successful sale.
///
/// Contains all the data needed to render or print a customer receipt without
/// any additional local DB lookups. Returned by both POST /sales (online sale)
/// and GET /sales/:id/receipt (re-fetch after connectivity is restored).
@JsonSerializable(explicitToJson: true)
class PosReceiptResponse {
  @JsonKey(name: 'sale_id')
  final String saleId;

  @JsonKey(name: 'session_id')
  final String? sessionId;

  @JsonKey(name: 'user_id')
  final String? userId;

  @JsonKey(name: 'sale_number')
  final String saleNumber;

  @JsonKey(defaultValue: 'COMPLETED')
  final String status;

  @JsonKey(name: 'sold_at')
  final DateTime soldAt;

  @JsonKey(name: 'branch_name')
  final String branchName;

  @JsonKey(name: 'branch_code', defaultValue: '')
  final String branchCode;
  @JsonKey(name: 'branch_address')
  final String? branchAddress;
  @JsonKey(name: 'branch_phone')
  final String? branchPhone;
  @JsonKey(name: 'business_name', defaultValue: '')
  final String businessName;
  @JsonKey(defaultValue: 'Rs.')
  final String currency;
  @JsonKey(name: 'receipt_logo_base64')
  final String? receiptLogoBase64;
  @JsonKey(name: 'receipt_tagline')
  final String? receiptTagline;
  @JsonKey(name: 'receipt_thank_you')
  final String? receiptThankYou;
  @JsonKey(name: 'receipt_terms')
  final String? receiptTerms;

  @JsonKey(name: 'cashier_name')
  final String cashierName;

  final List<PosReceiptItem> items;

  final String subtotal;
  final String discount;

  @JsonKey(name: 'tax_amount')
  final String taxAmount;

  /// Decimal rate string (e.g. "0.15"), or null when no tax was applied.
  @JsonKey(name: 'tax_rate')
  final String? taxRate;

  final String total;
  final List<PosReceiptPayment> payments;

  /// Amount of change due to the customer (total payments minus sale total).
  final String change;

  const PosReceiptResponse({
    required this.saleId,
    this.sessionId,
    this.userId,
    required this.saleNumber,
    this.status = 'COMPLETED',
    required this.soldAt,
    required this.branchName,
    this.branchCode = '',
    this.branchAddress,
    this.branchPhone,
    this.businessName = '',
    this.currency = 'Rs.',
    this.receiptLogoBase64,
    this.receiptTagline,
    this.receiptThankYou,
    this.receiptTerms,
    required this.cashierName,
    required this.items,
    required this.subtotal,
    required this.discount,
    required this.taxAmount,
    this.taxRate,
    required this.total,
    required this.payments,
    required this.change,
  });

  /// Constructs from the JSON body returned by POST /sales or GET /sales/:id/receipt.
  factory PosReceiptResponse.fromJson(Map<String, dynamic> json) =>
      _$PosReceiptResponseFromJson(json);

  Map<String, dynamic> toJson() => _$PosReceiptResponseToJson(this);
}
