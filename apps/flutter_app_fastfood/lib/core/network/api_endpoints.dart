/// Central registry of all POS API endpoint paths.
///
/// All paths are relative to the base URL configured in [buildDio].
/// Using a single abstract class prevents typo-induced 404s scattered
/// across multiple API service files.
abstract final class ApiEndpoints {
  static const String _base = '/api/v1/pos';

  // Auth
  /// One-time activation-code pairing. No token required.
  static const String activate = '$_base/auth/activate';
  static const String cashierLogin = '$_base/auth/cashier';
  static const String staffList = '$_base/auth/staff';
  static const String staffPin = '$_base/auth/staff-pin';

  // Sync
  static const String fullSync = '$_base/sync/full';
  static const String deltaSync = '$_base/sync/delta';
  static const String uploadOffline = '$_base/sync/upload';

  // Sales
  // Keep the canonical trailing slash. The backend also accepts the legacy
  // slashless path, but without this slash a catch-all static web mount can
  // turn an otherwise redirectable POST into HTTP 405.
  static const String createSale = '$_base/sales/';

  /// Receipt for a sale made by the calling cashier (own sales only).
  static String receiptById(String id) => '$_base/sales/$id/receipt';

  /// Explicit lookup of any branch sale by sale number — for cross-cashier reprint.
  static String receiptByNumber(String saleNumber) =>
      '$_base/sales/lookup?sale_number=${Uri.encodeComponent(saleNumber)}';
  static const String recentSales = '$_base/sales/recent';
  static String cancelSale(String id) => '$_base/sales/$id/cancel';
  static String returnSale(String id) => '$_base/sales/$id/return';

  // Session
  static const String openSession = '$_base/session/open';
  static const String closeSession = '$_base/session/close';
  static const String currentSession = '$_base/session/current';
  static const String sessionSummary = '$_base/session/summary';
  static const String sessionHistory = '$_base/session/history';

  /// Reconciliation summary for one past (closed) shift, by session id.
  static String sessionHistorySummary(String sessionId) =>
      '$_base/session/history/$sessionId/summary';

  // Device
  static const String heartbeat = '$_base/device/heartbeat';

  // Attendance
  static const String attendanceStaff = '$_base/attendance/staff';
  static const String attendancePunch = '$_base/attendance/punch';
  static const String attendanceStatus = '$_base/attendance/status';
}
