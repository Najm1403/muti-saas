// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'session_summary_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SessionSummaryResponse _$SessionSummaryResponseFromJson(
        Map<String, dynamic> json) =>
    SessionSummaryResponse(
      session:
          SessionResponse.fromJson(json['session'] as Map<String, dynamic>),
      summary: SessionSummary.fromJson(json['summary'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$SessionSummaryResponseToJson(
        SessionSummaryResponse instance) =>
    <String, dynamic>{
      'session': instance.session,
      'summary': instance.summary,
    };
