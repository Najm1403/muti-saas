// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pos_upload_result.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PosUploadResult _$PosUploadResultFromJson(Map<String, dynamic> json) =>
    PosUploadResult(
      saleNumber: json['sale_number'] as String,
      saleId: json['sale_id'] as String?,
      status: json['status'] as String,
      error: json['error'] as String?,
      retryable: json['retryable'] as bool? ?? true,
    );

Map<String, dynamic> _$PosUploadResultToJson(PosUploadResult instance) =>
    <String, dynamic>{
      'sale_number': instance.saleNumber,
      'sale_id': instance.saleId,
      'status': instance.status,
      'error': instance.error,
      'retryable': instance.retryable,
    };
