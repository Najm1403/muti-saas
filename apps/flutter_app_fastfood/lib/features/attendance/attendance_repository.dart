import '../../core/api/pos_attendance_api.dart';
import '../../core/models/attendance/attendance_punch_response.dart';
import '../../core/models/attendance/attendance_staff_member.dart';
import '../../core/models/attendance/attendance_status_entry.dart';

/// Thin wrapper over [PosAttendanceApi] — attendance never touches token
/// storage (no session is created), so unlike [AuthRepository] there is
/// nothing to persist here.
class AttendanceRepository {
  final PosAttendanceApi _api;

  AttendanceRepository(this._api);

  Future<List<AttendanceStaffMember>> staff() => _api.staff();

  Future<AttendancePunchResponse> punch(String employeeId, String pin) =>
      _api.punch(employeeId, pin);

  Future<List<AttendanceStatusEntry>> status() => _api.status();
}
