// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pos_sale_payment_create.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PosSalePaymentCreate _$PosSalePaymentCreateFromJson(
        Map<String, dynamic> json) =>
    PosSalePaymentCreate(
      paymentMethod: json['payment_method'] as String,
      amount: json['amount'] as String,
      reference: json['reference'] as String?,
    );

Map<String, dynamic> _$PosSalePaymentCreateToJson(
        PosSalePaymentCreate instance) =>
    <String, dynamic>{
      'payment_method': instance.paymentMethod,
      'amount': instance.amount,
      'reference': instance.reference,
    };
