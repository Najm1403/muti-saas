// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'device_activate_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

DeviceActivateResponse _$DeviceActivateResponseFromJson(
        Map<String, dynamic> json) =>
    DeviceActivateResponse(
      deviceToken: json['device_token'] as String,
      deviceId: json['device_id'] as String,
      deviceName: json['device_name'] as String,
      deviceType: json['device_type'] as String,
      deviceLetter: json['device_letter'] as String,
      branchId: json['branch_id'] as String,
      branchName: json['branch_name'] as String,
      businessId: json['business_id'] as String,
      businessName: json['business_name'] as String,
      tenantId: json['tenant_id'] as String,
      currency: json['currency'] as String,
    );

Map<String, dynamic> _$DeviceActivateResponseToJson(
        DeviceActivateResponse instance) =>
    <String, dynamic>{
      'device_token': instance.deviceToken,
      'device_id': instance.deviceId,
      'device_name': instance.deviceName,
      'device_type': instance.deviceType,
      'device_letter': instance.deviceLetter,
      'branch_id': instance.branchId,
      'branch_name': instance.branchName,
      'business_id': instance.businessId,
      'business_name': instance.businessName,
      'tenant_id': instance.tenantId,
      'currency': instance.currency,
    };
