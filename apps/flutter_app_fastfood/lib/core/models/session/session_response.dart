import 'package:json_annotation/json_annotation.dart';

part 'session_response.g.dart';

/// Session record returned by open, close, and current-session endpoints.
///
/// A session represents one cashier shift on one device. The POS uses
/// [status] to determine whether sales can be accepted ("OPEN") and
/// [id] to associate sales with the correct session on the server.
@JsonSerializable()
class SessionResponse {
  final String id;

  @JsonKey(name: 'device_id')
  final String deviceId;

  @JsonKey(name: 'user_id')
  final String userId;

  @JsonKey(name: 'branch_id')
  final String branchId;

  @JsonKey(name: 'tenant_id')
  final String tenantId;

  @JsonKey(name: 'opened_at')
  final DateTime openedAt;

  /// Null while the session is still open.
  @JsonKey(name: 'closed_at')
  final DateTime? closedAt;

  /// Cash in drawer at session start. Stored as String (Decimal).
  @JsonKey(name: 'opening_cash')
  final String openingCash;

  /// Cash in drawer at session end. Null until the session is closed.
  @JsonKey(name: 'closing_cash')
  final String? closingCash;

  /// "OPEN" while the shift is active; "CLOSED" after close is confirmed.
  final String status;

  final String? notes;

  @JsonKey(name: 'created_at')
  final DateTime createdAt;

  /// Human-readable shift code: YYMMDD + device letter + that device's
  /// Nth shift opened that day (1-based) — e.g. "260924A1". Null for
  /// shifts opened before the backend added this field.
  @JsonKey(name: 'shift_number')
  final String? shiftNumber;

  const SessionResponse({
    required this.id,
    required this.deviceId,
    required this.userId,
    required this.branchId,
    required this.tenantId,
    required this.openedAt,
    this.closedAt,
    required this.openingCash,
    this.closingCash,
    required this.status,
    this.notes,
    required this.createdAt,
    this.shiftNumber,
  });

  /// Constructs from the JSON body returned by session endpoints.
  factory SessionResponse.fromJson(Map<String, dynamic> json) =>
      _$SessionResponseFromJson(json);

  Map<String, dynamic> toJson() => _$SessionResponseToJson(this);
}
