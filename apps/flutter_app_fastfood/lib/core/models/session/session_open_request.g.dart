// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'session_open_request.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SessionOpenRequest _$SessionOpenRequestFromJson(Map<String, dynamic> json) =>
    SessionOpenRequest(
      openingCash: json['opening_cash'] as String? ?? '0.00',
      notes: json['notes'] as String?,
    );

Map<String, dynamic> _$SessionOpenRequestToJson(SessionOpenRequest instance) =>
    <String, dynamic>{
      'opening_cash': instance.openingCash,
      'notes': instance.notes,
    };
