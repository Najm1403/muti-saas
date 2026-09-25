// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'attendance_staff_member.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

AttendanceStaffMember _$AttendanceStaffMemberFromJson(
        Map<String, dynamic> json) =>
    AttendanceStaffMember(
      employeeId: json['employee_id'] as String,
      fullName: json['full_name'] as String,
      designation: json['designation'] as String?,
      hasPin: json['has_pin'] as bool,
    );

Map<String, dynamic> _$AttendanceStaffMemberToJson(
        AttendanceStaffMember instance) =>
    <String, dynamic>{
      'employee_id': instance.employeeId,
      'full_name': instance.fullName,
      'designation': instance.designation,
      'has_pin': instance.hasPin,
    };
