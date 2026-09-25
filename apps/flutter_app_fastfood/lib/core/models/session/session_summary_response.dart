import 'package:json_annotation/json_annotation.dart';

import 'session_response.dart';
import 'session_summary.dart';

part 'session_summary_response.g.dart';

/// The open session plus its live reconciliation summary.
///
/// Returned by GET /api/v1/pos/session/summary (cashier token).
@JsonSerializable()
class SessionSummaryResponse {
  final SessionResponse session;
  final SessionSummary summary;

  const SessionSummaryResponse({required this.session, required this.summary});

  factory SessionSummaryResponse.fromJson(Map<String, dynamic> json) =>
      _$SessionSummaryResponseFromJson(json);

  Map<String, dynamic> toJson() => _$SessionSummaryResponseToJson(this);
}
