import 'package:json_annotation/json_annotation.dart';

import 'session_response.dart';
import 'session_summary.dart';

part 'session_close_response.g.dart';

/// Returned by POST /api/v1/pos/session/close.
///
/// [variance] is `closing_cash - expected_cash` — positive means the drawer
/// held more than expected, negative means a shortfall.
@JsonSerializable()
class SessionCloseResponse {
  final SessionResponse session;
  final SessionSummary summary;
  final String variance;

  const SessionCloseResponse({
    required this.session,
    required this.summary,
    required this.variance,
  });

  factory SessionCloseResponse.fromJson(Map<String, dynamic> json) =>
      _$SessionCloseResponseFromJson(json);

  Map<String, dynamic> toJson() => _$SessionCloseResponseToJson(this);
}
