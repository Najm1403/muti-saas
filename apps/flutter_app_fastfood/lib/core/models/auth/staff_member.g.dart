// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'staff_member.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

StaffMember _$StaffMemberFromJson(Map<String, dynamic> json) => StaffMember(
      userId: json['user_id'] as String,
      fullName: json['full_name'] as String,
      designation: json['designation'] as String,
      photoUrl: json['photo_url'] as String?,
      hasPin: json['has_pin'] as bool,
    );

Map<String, dynamic> _$StaffMemberToJson(StaffMember instance) =>
    <String, dynamic>{
      'user_id': instance.userId,
      'full_name': instance.fullName,
      'designation': instance.designation,
      'photo_url': instance.photoUrl,
      'has_pin': instance.hasPin,
    };
