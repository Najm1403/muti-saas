import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../core/models/session/session_close_response.dart';
import '../core/models/session/session_response.dart';
import '../core/models/session/session_summary_response.dart';
import '../core/network/api_exception.dart';
import 'auth_notifier.dart';
import 'repository_providers.dart';

part 'session_notifier.g.dart';

/// Manages the cashier shift session for the lifetime of the app.
///
/// [build] fetches the current open session from the server whenever a cashier
/// is logged in. Returns null when no session is open (prompts the router to
/// redirect to /session/open). Session data is online-only — the server is
/// authoritative for opening/closing times and cash reconciliation.
@Riverpod(keepAlive: true)
class SessionNotifier extends _$SessionNotifier {
  @override
  Future<SessionResponse?> build() async {
    final auth = await ref.watch(authNotifierProvider.future);
    if (!auth.isCashierLoggedIn) return null;

    try {
      return await ref.read(sessionRepositoryProvider).currentSession();
    } on ApiException catch (e) {
      // 404 means no open session — user needs to open one.
      if (e.isNotFound) return null;
      rethrow;
    }
  }

  /// Opens a new shift session and updates state on success.
  ///
  /// [openingCash] defaults to '0.00' when the cashier skips the count step.
  Future<void> openSession({
    String openingCash = '0.00',
    String? notes,
  }) async {
    final session = await ref
        .read(sessionRepositoryProvider)
        .openSession(openingCash: openingCash, notes: notes);
    state = AsyncData(session);
  }

  /// Closes the current shift session and clears local state.
  ///
  /// Returns the [SessionCloseResponse] (summary + variance) for the close
  /// screen. After closing, state becomes null, triggering a router redirect
  /// back to the staff picker.
  Future<SessionCloseResponse> closeSession({
    required String closingCash,
    String? notes,
  }) async {
    final res = await ref
        .read(sessionRepositoryProvider)
        .closeSession(closingCash: closingCash, notes: notes);
    state = const AsyncData(null);
    return res;
  }

  /// Live reconciliation summary for the current open shift (for the close screen).
  Future<SessionSummaryResponse> summary() =>
      ref.read(sessionRepositoryProvider).summary();
}
