// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pos_receipt_payment.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PosReceiptPayment _$PosReceiptPaymentFromJson(Map<String, dynamic> json) =>
    PosReceiptPayment(
      paymentMethod: json['payment_method'] as String,
      amount: json['amount'] as String,
      reference: json['reference'] as String?,
    );

Map<String, dynamic> _$PosReceiptPaymentToJson(PosReceiptPayment instance) =>
    <String, dynamic>{
      'payment_method': instance.paymentMethod,
      'amount': instance.amount,
      'reference': instance.reference,
    };
