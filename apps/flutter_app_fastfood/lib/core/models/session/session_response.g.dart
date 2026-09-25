// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'session_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SessionResponse _$SessionResponseFromJson(Map<String, dynamic> json) =>
    SessionResponse(
      id: json['id'] as String,
      deviceId: json['device_id'] as String,
      userId: json['user_id'] as String,
      branchId: json['branch_id'] as String,
      tenantId: json['tenant_id'] as String,
      openedAt: DateTime.parse(json['opened_at'] as String),
      closedAt: json['closed_at'] == null
          ? null
          : DateTime.parse(json['closed_at'] as String),
      openingCash: json['opening_cash'] as String,
      closingCash: json['closing_cash'] as String?,
      status: json['status'] as String,
      notes: json['notes'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
      shiftNumber: json['shift_number'] as String?,
    );

Map<String, dynamic> _$SessionResponseToJson(SessionResponse instance) =>
    <String, dynamic>{
      'id': instance.id,
      'device_id': instance.deviceId,
      'user_id': instance.userId,
      'branch_id': instance.branchId,
      'tenant_id': instance.tenantId,
      'opened_at': instance.openedAt.toIso8601String(),
      'closed_at': instance.closedAt?.toIso8601String(),
      'opening_cash': instance.openingCash,
      'closing_cash': instance.closingCash,
      'status': instance.status,
      'notes': instance.notes,
      'created_at': instance.createdAt.toIso8601String(),
      'shift_number': instance.shiftNumber,
    };
