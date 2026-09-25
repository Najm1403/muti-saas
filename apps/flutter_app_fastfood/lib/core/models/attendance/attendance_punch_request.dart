import 'package:json_annotation/json_annotation.dart';

part 'attendance_punch_request.g.dart';

/// Body for POST /api/v1/pos/attendance/punch (device token).
///
/// Sent after a staff member is tapped on the attendance grid and enters
/// their PIN. Verified against the employee's own attendance PIN — no User
/// account required — and never mints a cashier token; this cannot be used
/// to gain POS access, only to clock in/out.
@JsonSerializable()
class AttendancePunchRequest {
  @JsonKey(name: 'employee_id')
  final String employeeId;

  final String pin;

  const AttendancePunchRequest({required this.employeeId, required this.pin});

  factory AttendancePunchRequest.fromJson(Map<String, dynamic> json) =>
      _$AttendancePunchRequestFromJson(json);

  Map<String, dynamic> toJson() => _$AttendancePunchRequestToJson(this);
}
