// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'attendance_punch_request.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

AttendancePunchRequest _$AttendancePunchRequestFromJson(
        Map<String, dynamic> json) =>
    AttendancePunchRequest(
      employeeId: json['employee_id'] as String,
      pin: json['pin'] as String,
    );

Map<String, dynamic> _$AttendancePunchRequestToJson(
        AttendancePunchRequest instance) =>
    <String, dynamic>{
      'employee_id': instance.employeeId,
      'pin': instance.pin,
    };
