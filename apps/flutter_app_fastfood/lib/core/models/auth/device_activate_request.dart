import 'package:json_annotation/json_annotation.dart';

part 'device_activate_request.g.dart';

/// Request body for POST /api/v1/pos/auth/activate.
///
/// [activationCode] is the one-time 4-digit code the tenant generated in the
/// web dashboard (shown grouped as "58 32"; sent digits-only). After a
/// successful activation the returned device_token takes over.
@JsonSerializable(includeIfNull: false)
class DeviceActivateRequest {
  @JsonKey(name: 'activation_code')
  final String activationCode;

  /// Reported for the device record — e.g. "android", "windows".
  final String? platform;

  @JsonKey(name: 'app_version')
  final String? appVersion;

  const DeviceActivateRequest({
    required this.activationCode,
    this.platform,
    this.appVersion,
  });

  factory DeviceActivateRequest.fromJson(Map<String, dynamic> json) =>
      _$DeviceActivateRequestFromJson(json);

  Map<String, dynamic> toJson() => _$DeviceActivateRequestToJson(this);
}
