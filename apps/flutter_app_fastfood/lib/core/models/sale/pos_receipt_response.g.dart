// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pos_receipt_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PosReceiptResponse _$PosReceiptResponseFromJson(Map<String, dynamic> json) =>
    PosReceiptResponse(
      saleId: json['sale_id'] as String,
      sessionId: json['session_id'] as String?,
      userId: json['user_id'] as String?,
      saleNumber: json['sale_number'] as String,
      status: json['status'] as String? ?? 'COMPLETED',
      soldAt: DateTime.parse(json['sold_at'] as String),
      branchName: json['branch_name'] as String,
      branchCode: json['branch_code'] as String? ?? '',
      branchAddress: json['branch_address'] as String?,
      branchPhone: json['branch_phone'] as String?,
      businessName: json['business_name'] as String? ?? '',
      currency: json['currency'] as String? ?? 'Rs.',
      receiptLogoBase64: json['receipt_logo_base64'] as String?,
      receiptTagline: json['receipt_tagline'] as String?,
      receiptThankYou: json['receipt_thank_you'] as String?,
      receiptTerms: json['receipt_terms'] as String?,
      cashierName: json['cashier_name'] as String,
      items: (json['items'] as List<dynamic>)
          .map((e) => PosReceiptItem.fromJson(e as Map<String, dynamic>))
          .toList(),
      subtotal: json['subtotal'] as String,
      discount: json['discount'] as String,
      taxAmount: json['tax_amount'] as String,
      taxRate: json['tax_rate'] as String?,
      total: json['total'] as String,
      payments: (json['payments'] as List<dynamic>)
          .map((e) => PosReceiptPayment.fromJson(e as Map<String, dynamic>))
          .toList(),
      change: json['change'] as String,
    );

Map<String, dynamic> _$PosReceiptResponseToJson(PosReceiptResponse instance) =>
    <String, dynamic>{
      'sale_id': instance.saleId,
      'session_id': instance.sessionId,
      'user_id': instance.userId,
      'sale_number': instance.saleNumber,
      'status': instance.status,
      'sold_at': instance.soldAt.toIso8601String(),
      'branch_name': instance.branchName,
      'branch_code': instance.branchCode,
      'branch_address': instance.branchAddress,
      'branch_phone': instance.branchPhone,
      'business_name': instance.businessName,
      'currency': instance.currency,
      'receipt_logo_base64': instance.receiptLogoBase64,
      'receipt_tagline': instance.receiptTagline,
      'receipt_thank_you': instance.receiptThankYou,
      'receipt_terms': instance.receiptTerms,
      'cashier_name': instance.cashierName,
      'items': instance.items.map((e) => e.toJson()).toList(),
      'subtotal': instance.subtotal,
      'discount': instance.discount,
      'tax_amount': instance.taxAmount,
      'tax_rate': instance.taxRate,
      'total': instance.total,
      'payments': instance.payments.map((e) => e.toJson()).toList(),
      'change': instance.change,
    };
