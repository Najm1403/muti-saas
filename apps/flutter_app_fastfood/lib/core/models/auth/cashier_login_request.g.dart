// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'cashier_login_request.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CashierLoginRequest _$CashierLoginRequestFromJson(Map<String, dynamic> json) =>
    CashierLoginRequest(
      username: json['username'] as String,
      password: json['password'] as String,
    );

Map<String, dynamic> _$CashierLoginRequestToJson(
        CashierLoginRequest instance) =>
    <String, dynamic>{
      'username': instance.username,
      'password': instance.password,
    };
