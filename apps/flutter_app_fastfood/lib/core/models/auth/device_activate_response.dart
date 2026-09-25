import 'package:json_annotation/json_annotation.dart';

part 'device_activate_response.g.dart';

/// Payload returned by POST /api/v1/pos/auth/activate.
///
/// [deviceToken] is a long-lived credential (~30 days) stored in
/// flutter_secure_storage. The remaining fields are everything the first-install
/// screen needs to configure the app — no follow-up call required.
@JsonSerializable()
class DeviceActivateResponse {
  @JsonKey(name: 'device_token')
  final String deviceToken;

  @JsonKey(name: 'device_id')
  final String deviceId;

  @JsonKey(name: 'device_name')
  final String deviceName;

  @JsonKey(name: 'device_type')
  final String deviceType;

  /// Auto-assigned, permanent per-branch label (A, B, C, ...) — folded into
  /// every sale_number this device generates so two devices at the same
  /// branch can never produce the same number offline. See
  /// SaleRepository.createSale().
  @JsonKey(name: 'device_letter')
  final String deviceLetter;

  @JsonKey(name: 'branch_id')
  final String branchId;

  @JsonKey(name: 'branch_name')
  final String branchName;

  @JsonKey(name: 'business_id')
  final String businessId;

  @JsonKey(name: 'business_name')
  final String businessName;

  @JsonKey(name: 'tenant_id')
  final String tenantId;

  final String currency;

  const DeviceActivateResponse({
    required this.deviceToken,
    required this.deviceId,
    required this.deviceName,
    required this.deviceType,
    required this.deviceLetter,
    required this.branchId,
    required this.branchName,
    required this.businessId,
    required this.businessName,
    required this.tenantId,
    required this.currency,
  });

  factory DeviceActivateResponse.fromJson(Map<String, dynamic> json) =>
      _$DeviceActivateResponseFromJson(json);

  Map<String, dynamic> toJson() => _$DeviceActivateResponseToJson(this);
}
