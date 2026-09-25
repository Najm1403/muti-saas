// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pos_delta_sync_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PosDeltaSyncResponse _$PosDeltaSyncResponseFromJson(
        Map<String, dynamic> json) =>
    PosDeltaSyncResponse(
      branchId: json['branch_id'] as String,
      since: DateTime.parse(json['since'] as String),
      syncedAt: DateTime.parse(json['synced_at'] as String),
      categories: (json['categories'] as List<dynamic>?)
              ?.map((e) => PosSyncCategory.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      products: (json['products'] as List<dynamic>?)
              ?.map((e) => PosSyncProduct.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      taxRates: (json['tax_rates'] as List<dynamic>?)
              ?.map((e) => PosSyncTaxRate.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      deals: (json['deals'] as List<dynamic>?)
              ?.map((e) => PosSyncDeal.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      promotions: (json['promotions'] as List<dynamic>?)
              ?.map((e) => PosSyncPromotion.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
    );

Map<String, dynamic> _$PosDeltaSyncResponseToJson(
        PosDeltaSyncResponse instance) =>
    <String, dynamic>{
      'branch_id': instance.branchId,
      'since': instance.since.toIso8601String(),
      'synced_at': instance.syncedAt.toIso8601String(),
      'categories': instance.categories.map((e) => e.toJson()).toList(),
      'products': instance.products.map((e) => e.toJson()).toList(),
      'tax_rates': instance.taxRates.map((e) => e.toJson()).toList(),
      'deals': instance.deals.map((e) => e.toJson()).toList(),
      'promotions': instance.promotions.map((e) => e.toJson()).toList(),
    };
