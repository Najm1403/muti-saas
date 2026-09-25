// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pos_upload_request.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PosUploadRequest _$PosUploadRequestFromJson(Map<String, dynamic> json) =>
    PosUploadRequest(
      sales: (json['sales'] as List<dynamic>)
          .map((e) => PosOfflineSale.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$PosUploadRequestToJson(PosUploadRequest instance) =>
    <String, dynamic>{
      'sales': instance.sales.map((e) => e.toJson()).toList(),
    };
