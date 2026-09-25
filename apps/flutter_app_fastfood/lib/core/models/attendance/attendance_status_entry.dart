import 'package:json_annotation/json_annotation.dart';

part 'attendance_status_entry.g.dart';

/// One currently-clocked-in employee, from GET /api/v1/pos/attendance/status.
///
/// Powers the "clocked in since ..." badge on the attendance staff grid.
@JsonSerializable()
class AttendanceStatusEntry {
  @JsonKey(name: 'employee_id')
  final String employeeId;

  @JsonKey(name: 'user_id')
  final String? userId;

  @JsonKey(name: 'full_name')
  final String fullName;

  @JsonKey(name: 'clock_in_at')
  final DateTime clockInAt;

  const AttendanceStatusEntry({
    required this.employeeId,
    this.userId,
    required this.fullName,
    required this.clockInAt,
  });

  factory AttendanceStatusEntry.fromJson(Map<String, dynamic> json) =>
      _$AttendanceStatusEntryFromJson(json);

  Map<String, dynamic> toJson() => _$AttendanceStatusEntryToJson(this);
}
