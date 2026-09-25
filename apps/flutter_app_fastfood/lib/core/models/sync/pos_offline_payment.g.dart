// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pos_offline_payment.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PosOfflinePayment _$PosOfflinePaymentFromJson(Map<String, dynamic> json) =>
    PosOfflinePayment(
      paymentMethod: json['payment_method'] as String,
      amount: json['amount'] as String,
      reference: json['reference'] as String?,
    );

Map<String, dynamic> _$PosOfflinePaymentToJson(PosOfflinePayment instance) =>
    <String, dynamic>{
      'payment_method': instance.paymentMethod,
      'amount': instance.amount,
      'reference': instance.reference,
    };
