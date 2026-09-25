// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'session_close_request.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SessionCloseRequest _$SessionCloseRequestFromJson(Map<String, dynamic> json) =>
    SessionCloseRequest(
      closingCash: json['closing_cash'] as String,
      notes: json['notes'] as String?,
    );

Map<String, dynamic> _$SessionCloseRequestToJson(
        SessionCloseRequest instance) =>
    <String, dynamic>{
      'closing_cash': instance.closingCash,
      'notes': instance.notes,
    };
