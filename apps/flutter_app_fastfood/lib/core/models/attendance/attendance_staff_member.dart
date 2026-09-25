import 'package:json_annotation/json_annotation.dart';

part 'attendance_staff_member.g.dart';

/// One active employee on the attendance clock-in grid, from
/// GET /api/v1/pos/attendance/staff (device token).
///
/// Independent of [StaffMember] (the cashier picker, sourced from Users) —
/// every active employee appears here whether or not they're also a User,
/// since attendance is authenticated with the employee's own PIN, not a
/// User's. [hasPin] tells the UI whether tapping this tile should open the
/// PIN pad or a "no PIN set — ask an admin" hint.
@JsonSerializable()
class AttendanceStaffMember {
  @JsonKey(name: 'employee_id')
  final String employeeId;

  @JsonKey(name: 'full_name')
  final String fullName;

  final String? designation;

  @JsonKey(name: 'has_pin')
  final bool hasPin;

  const AttendanceStaffMember({
    required this.employeeId,
    required this.fullName,
    this.designation,
    required this.hasPin,
  });

  /// First letters of the name, for the initials avatar.
  String get initials {
    final parts = fullName
        .trim()
        .split(RegExp(r'\s+'))
        .where((p) => p.isNotEmpty)
        .toList();
    if (parts.isEmpty) return '?';
    if (parts.length == 1) return parts.first.substring(0, 1).toUpperCase();
    return (parts.first.substring(0, 1) + parts.last.substring(0, 1))
        .toUpperCase();
  }

  factory AttendanceStaffMember.fromJson(Map<String, dynamic> json) =>
      _$AttendanceStaffMemberFromJson(json);

  Map<String, dynamic> toJson() => _$AttendanceStaffMemberToJson(this);
}
