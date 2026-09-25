// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'attendance_status_entry.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

AttendanceStatusEntry _$AttendanceStatusEntryFromJson(
        Map<String, dynamic> json) =>
    AttendanceStatusEntry(
      employeeId: json['employee_id'] as String,
      userId: json['user_id'] as String?,
      fullName: json['full_name'] as String,
      clockInAt: DateTime.parse(json['clock_in_at'] as String),
    );

Map<String, dynamic> _$AttendanceStatusEntryToJson(
        AttendanceStatusEntry instance) =>
    <String, dynamic>{
      'employee_id': instance.employeeId,
      'user_id': instance.userId,
      'full_name': instance.fullName,
      'clock_in_at': instance.clockInAt.toIso8601String(),
    };
