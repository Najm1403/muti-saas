import 'package:json_annotation/json_annotation.dart';

part 'staff_pin_request.g.dart';

/// Body for POST /api/v1/pos/auth/staff-pin (device token).
///
/// Sent after a staff member is tapped on the grid and enters their PIN.
/// The response is a [CashierLoginResponse].
@JsonSerializable()
class StaffPinRequest {
  @JsonKey(name: 'user_id')
  final String userId;

  final String pin;

  const StaffPinRequest({required this.userId, required this.pin});

  factory StaffPinRequest.fromJson(Map<String, dynamic> json) =>
      _$StaffPinRequestFromJson(json);

  Map<String, dynamic> toJson() => _$StaffPinRequestToJson(this);
}
