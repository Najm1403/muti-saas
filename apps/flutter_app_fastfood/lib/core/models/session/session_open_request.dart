import 'package:json_annotation/json_annotation.dart';

part 'session_open_request.g.dart';

/// Request body sent when a cashier opens a new shift session.
///
/// [openingCash] is the physical cash count in the drawer at session start,
/// recorded for reconciliation at close. Defaults to '0.00' when not counted.
@JsonSerializable()
class SessionOpenRequest {
  /// Cash in drawer at session start. Stored as String (Decimal).
  @JsonKey(name: 'opening_cash')
  final String openingCash;

  final String? notes;

  const SessionOpenRequest({
    this.openingCash = '0.00',
    this.notes,
  });

  factory SessionOpenRequest.fromJson(Map<String, dynamic> json) =>
      _$SessionOpenRequestFromJson(json);

  /// Serializes the body for POST /session/open.
  Map<String, dynamic> toJson() => _$SessionOpenRequestToJson(this);
}
