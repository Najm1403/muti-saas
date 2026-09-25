import 'package:json_annotation/json_annotation.dart';

part 'staff_member.g.dart';

/// One active staff member on the tablet's staff-picker grid.
///
/// Returned by GET /api/v1/pos/auth/staff (device token). [designation] is the
/// member's role name; [hasPin] tells the UI whether to show the PIN pad or a
/// "no PIN set" hint (login then falls back to the web password server-side).
@JsonSerializable()
class StaffMember {
  @JsonKey(name: 'user_id')
  final String userId;

  @JsonKey(name: 'full_name')
  final String fullName;

  final String designation;

  @JsonKey(name: 'photo_url')
  final String? photoUrl;

  @JsonKey(name: 'has_pin')
  final bool hasPin;

  const StaffMember({
    required this.userId,
    required this.fullName,
    required this.designation,
    this.photoUrl,
    required this.hasPin,
  });

  /// First letters of the name, for the initials avatar.
  String get initials {
    final parts = fullName
        .trim()
        .split(RegExp(r'\s+'))
        .where((p) => p.isNotEmpty)
        .toList();
    if (parts.isEmpty) return '?';
    if (parts.length == 1) return parts.first.substring(0, 1).toUpperCase();
    return (parts.first.substring(0, 1) + parts.last.substring(0, 1))
        .toUpperCase();
  }

  factory StaffMember.fromJson(Map<String, dynamic> json) =>
      _$StaffMemberFromJson(json);

  Map<String, dynamic> toJson() => _$StaffMemberToJson(this);
}
