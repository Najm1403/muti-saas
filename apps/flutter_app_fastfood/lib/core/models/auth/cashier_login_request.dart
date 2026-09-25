import 'package:json_annotation/json_annotation.dart';

part 'cashier_login_request.g.dart';

/// Credentials sent when a cashier signs in at the start of a shift.
///
/// Authentication is performed against the device's assigned branch,
/// so no tenant or branch ID is needed in the body — the device_token
/// header already scopes the request.
@JsonSerializable()
class CashierLoginRequest {
  final String username;
  final String password;

  const CashierLoginRequest({required this.username, required this.password});

  /// Constructs from JSON (symmetric with [toJson], required by json_serializable).
  factory CashierLoginRequest.fromJson(Map<String, dynamic> json) =>
      _$CashierLoginRequestFromJson(json);

  /// Serializes the body for POST /auth/cashier.
  Map<String, dynamic> toJson() => _$CashierLoginRequestToJson(this);
}
