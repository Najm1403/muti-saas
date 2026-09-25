// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'device_activate_request.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

DeviceActivateRequest _$DeviceActivateRequestFromJson(
        Map<String, dynamic> json) =>
    DeviceActivateRequest(
      activationCode: json['activation_code'] as String,
      platform: json['platform'] as String?,
      appVersion: json['app_version'] as String?,
    );

Map<String, dynamic> _$DeviceActivateRequestToJson(
        DeviceActivateRequest instance) =>
    <String, dynamic>{
      'activation_code': instance.activationCode,
      if (instance.platform case final value?) 'platform': value,
      if (instance.appVersion case final value?) 'app_version': value,
    };
