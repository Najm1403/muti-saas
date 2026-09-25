import 'package:json_annotation/json_annotation.dart';

part 'session_close_request.g.dart';

/// Request body sent when a cashier closes their shift session.
///
/// [closingCash] is the physical cash count after removing the opening float,
/// used by the back-office to calculate cash variance for the session.
@JsonSerializable()
class SessionCloseRequest {
  /// Cash in drawer at session end. Stored as String (Decimal).
  @JsonKey(name: 'closing_cash')
  final String closingCash;

  final String? notes;

  const SessionCloseRequest({
    required this.closingCash,
    this.notes,
  });

  factory SessionCloseRequest.fromJson(Map<String, dynamic> json) =>
      _$SessionCloseRequestFromJson(json);

  /// Serializes the body for POST /session/close.
  Map<String, dynamic> toJson() => _$SessionCloseRequestToJson(this);
}
