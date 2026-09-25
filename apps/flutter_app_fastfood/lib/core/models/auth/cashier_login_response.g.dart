// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'cashier_login_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CashierLoginResponse _$CashierLoginResponseFromJson(
        Map<String, dynamic> json) =>
    CashierLoginResponse(
      cashierToken: json['cashier_token'] as String,
      offlineProof: json['offline_proof'] as String?,
      userId: json['user_id'] as String,
      fullName: json['full_name'] as String,
      deviceId: json['device_id'] as String,
      branchId: json['branch_id'] as String,
      tenantId: json['tenant_id'] as String,
    );

Map<String, dynamic> _$CashierLoginResponseToJson(
        CashierLoginResponse instance) =>
    <String, dynamic>{
      'cashier_token': instance.cashierToken,
      'offline_proof': instance.offlineProof,
      'user_id': instance.userId,
      'full_name': instance.fullName,
      'device_id': instance.deviceId,
      'branch_id': instance.branchId,
      'tenant_id': instance.tenantId,
    };
