import '../../core/api/pos_session_api.dart';
import '../../core/models/session/session_close_request.dart';
import '../../core/models/session/session_close_response.dart';
import '../../core/models/session/session_open_request.dart';
import '../../core/models/session/session_response.dart';
import '../../core/models/session/session_summary_response.dart';

/// Manages the cashier shift session lifecycle.
///
/// Thin wrapper around [PosSessionApi] that presents a cleaner interface
/// to feature/UI code. Sessions must be managed online — there is no
/// offline session fallback because the server is authoritative for
/// opening/closing times and cash reconciliation.
class SessionRepository {
  final PosSessionApi _api;

  SessionRepository(this._api);

  /// Opens a new shift session with the given [openingCash] amount.
  ///
  /// [openingCash] defaults to '0.00' when the drawer is not counted.
  /// Throws [ApiException] if a session is already open on this device.
  Future<SessionResponse> openSession({
    String openingCash = '0.00',
    String? notes,
  }) =>
      _api.openSession(SessionOpenRequest(openingCash: openingCash, notes: notes));

  /// Closes the current shift session recording [closingCash] in the drawer.
  ///
  /// Returns the [SessionCloseResponse] with the reconciliation summary and
  /// cash variance. Throws [ApiException] with 404 if no open session exists.
  Future<SessionCloseResponse> closeSession({
    required String closingCash,
    String? notes,
  }) =>
      _api.closeSession(SessionCloseRequest(closingCash: closingCash, notes: notes));

  /// Returns the currently open session for this device, if any.
  ///
  /// Throws [ApiException] with 404 when no session is open — callers
  /// should treat 404 as a prompt to open a new session.
  Future<SessionResponse> currentSession() => _api.currentSession();

  /// Live reconciliation summary for the current open shift.
  Future<SessionSummaryResponse> summary() => _api.sessionSummary();

  /// This cashier's past (closed) shifts, newest first.
  Future<List<SessionResponse>> history() => _api.history();

  /// Full reconciliation summary for one past shift by [sessionId] — works
  /// after the shift is closed, not just at the moment of closing.
  Future<SessionSummaryResponse> historySummary(String sessionId) =>
      _api.historySummary(sessionId);
}
