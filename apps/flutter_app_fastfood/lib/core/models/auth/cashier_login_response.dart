import 'package:json_annotation/json_annotation.dart';

part 'cashier_login_response.g.dart';

/// Payload returned after a successful cashier login.
///
/// [cashierToken] is a short-lived credential (12 h) kept in-memory only —
/// it is never written to disk so that clearing app memory automatically
/// signs the cashier out on restart.
@JsonSerializable()
class CashierLoginResponse {
  @JsonKey(name: 'cashier_token')
  final String cashierToken;

  @JsonKey(name: 'offline_proof')
  final String? offlineProof;

  @JsonKey(name: 'user_id')
  final String userId;

  @JsonKey(name: 'full_name')
  final String fullName;

  @JsonKey(name: 'device_id')
  final String deviceId;

  @JsonKey(name: 'branch_id')
  final String branchId;

  @JsonKey(name: 'tenant_id')
  final String tenantId;

  const CashierLoginResponse({
    required this.cashierToken,
    this.offlineProof,
    required this.userId,
    required this.fullName,
    required this.deviceId,
    required this.branchId,
    required this.tenantId,
  });

  /// Constructs from the JSON body returned by POST /auth/cashier.
  factory CashierLoginResponse.fromJson(Map<String, dynamic> json) =>
      _$CashierLoginResponseFromJson(json);

  Map<String, dynamic> toJson() => _$CashierLoginResponseToJson(this);
}
