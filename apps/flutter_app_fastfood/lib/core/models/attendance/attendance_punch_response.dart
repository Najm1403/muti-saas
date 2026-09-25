import 'package:json_annotation/json_annotation.dart';

part 'attendance_punch_response.g.dart';

/// Response from POST /api/v1/pos/attendance/punch.
///
/// [action] toggles automatically server-side: "clocked_in" when no open
/// record existed for this employee, "clocked_out" when one did.
@JsonSerializable()
class AttendancePunchResponse {
  final String id;

  @JsonKey(name: 'employee_id')
  final String employeeId;

  @JsonKey(name: 'full_name')
  final String fullName;

  /// "clocked_in" | "clocked_out"
  final String action;

  @JsonKey(name: 'clock_in_at')
  final DateTime clockInAt;

  @JsonKey(name: 'clock_out_at')
  final DateTime? clockOutAt;

  const AttendancePunchResponse({
    required this.id,
    required this.employeeId,
    required this.fullName,
    required this.action,
    required this.clockInAt,
    this.clockOutAt,
  });

  bool get clockedIn => action == 'clocked_in';

  factory AttendancePunchResponse.fromJson(Map<String, dynamic> json) =>
      _$AttendancePunchResponseFromJson(json);

  Map<String, dynamic> toJson() => _$AttendancePunchResponseToJson(this);
}
