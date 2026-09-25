// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'attendance_punch_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

AttendancePunchResponse _$AttendancePunchResponseFromJson(
        Map<String, dynamic> json) =>
    AttendancePunchResponse(
      id: json['id'] as String,
      employeeId: json['employee_id'] as String,
      fullName: json['full_name'] as String,
      action: json['action'] as String,
      clockInAt: DateTime.parse(json['clock_in_at'] as String),
      clockOutAt: json['clock_out_at'] == null
          ? null
          : DateTime.parse(json['clock_out_at'] as String),
    );

Map<String, dynamic> _$AttendancePunchResponseToJson(
        AttendancePunchResponse instance) =>
    <String, dynamic>{
      'id': instance.id,
      'employee_id': instance.employeeId,
      'full_name': instance.fullName,
      'action': instance.action,
      'clock_in_at': instance.clockInAt.toIso8601String(),
      'clock_out_at': instance.clockOutAt?.toIso8601String(),
    };
