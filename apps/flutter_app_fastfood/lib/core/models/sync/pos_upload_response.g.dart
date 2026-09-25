// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pos_upload_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PosUploadResponse _$PosUploadResponseFromJson(Map<String, dynamic> json) =>
    PosUploadResponse(
      total: (json['total'] as num).toInt(),
      created: (json['created'] as num).toInt(),
      duplicates: (json['duplicates'] as num).toInt(),
      errors: (json['errors'] as num).toInt(),
      results: (json['results'] as List<dynamic>?)
              ?.map((e) => PosUploadResult.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
    );

Map<String, dynamic> _$PosUploadResponseToJson(PosUploadResponse instance) =>
    <String, dynamic>{
      'total': instance.total,
      'created': instance.created,
      'duplicates': instance.duplicates,
      'errors': instance.errors,
      'results': instance.results.map((e) => e.toJson()).toList(),
    };
