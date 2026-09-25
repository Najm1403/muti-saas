// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'session_close_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SessionCloseResponse _$SessionCloseResponseFromJson(
        Map<String, dynamic> json) =>
    SessionCloseResponse(
      session:
          SessionResponse.fromJson(json['session'] as Map<String, dynamic>),
      summary: SessionSummary.fromJson(json['summary'] as Map<String, dynamic>),
      variance: json['variance'] as String,
    );

Map<String, dynamic> _$SessionCloseResponseToJson(
        SessionCloseResponse instance) =>
    <String, dynamic>{
      'session': instance.session,
      'summary': instance.summary,
      'variance': instance.variance,
    };
