// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'staff_pin_request.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

StaffPinRequest _$StaffPinRequestFromJson(Map<String, dynamic> json) =>
    StaffPinRequest(
      userId: json['user_id'] as String,
      pin: json['pin'] as String,
    );

Map<String, dynamic> _$StaffPinRequestToJson(StaffPinRequest instance) =>
    <String, dynamic>{
      'user_id': instance.userId,
      'pin': instance.pin,
    };
