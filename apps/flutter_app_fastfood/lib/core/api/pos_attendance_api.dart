import 'package:dio/dio.dart';

import '../models/attendance/attendance_punch_request.dart';
import '../models/attendance/attendance_punch_response.dart';
import '../models/attendance/attendance_staff_member.dart';
import '../models/attendance/attendance_status_entry.dart';
import '../network/api_endpoints.dart';
import '../network/api_exception.dart';

/// HTTP client for POS attendance clock-in/out.
///
/// All endpoints are device-token routes (see [usesDeviceTokenForPath]) —
/// no cashier session is required or created by any of them.
class PosAttendanceApi {
  final Dio _dio;

  PosAttendanceApi(this._dio);

  /// Active employees for this device's branch — powers the attendance grid.
  /// Every active employee appears here, whether or not they're also a User.
  Future<List<AttendanceStaffMember>> staff() async {
    try {
      final res = await _dio.get(ApiEndpoints.attendanceStaff);
      return (res.data as List)
          .map((e) => AttendanceStaffMember.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw e.error is ApiException ? e.error as ApiException : ApiException(message: e.message ?? 'Unknown error');
    }
  }

  /// Toggles attendance for [employeeId]: clocks in if no open record
  /// exists, clocks out if one does. Throws [ApiException] on an invalid
  /// PIN (401) or when the employee has no attendance PIN set (422).
  Future<AttendancePunchResponse> punch(String employeeId, String pin) async {
    try {
      final res = await _dio.post(
        ApiEndpoints.attendancePunch,
        data: AttendancePunchRequest(employeeId: employeeId, pin: pin).toJson(),
      );
      return AttendancePunchResponse.fromJson(res.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw e.error is ApiException ? e.error as ApiException : ApiException(message: e.message ?? 'Unknown error');
    }
  }

  /// Employees currently clocked in at this device's branch.
  Future<List<AttendanceStatusEntry>> status() async {
    try {
      final res = await _dio.get(ApiEndpoints.attendanceStatus);
      return (res.data as List)
          .map((e) => AttendanceStatusEntry.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw e.error is ApiException ? e.error as ApiException : ApiException(message: e.message ?? 'Unknown error');
    }
  }
}
