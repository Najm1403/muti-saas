// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pos_sync_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PosSyncResponse _$PosSyncResponseFromJson(Map<String, dynamic> json) =>
    PosSyncResponse(
      branchId: json['branch_id'] as String,
      branchName: json['branch_name'] as String,
      branchCode: json['branch_code'] as String,
      branchAddress: json['branch_address'] as String?,
      branchPhone: json['branch_phone'] as String?,
      businessName: json['business_name'] as String,
      receiptLogoBase64: json['receipt_logo_base64'] as String?,
      receiptTagline: json['receipt_tagline'] as String?,
      receiptThankYou: json['receipt_thank_you'] as String?,
      receiptTerms: json['receipt_terms'] as String?,
      currency: json['currency'] as String? ?? 'Rs.',
      lowStockThreshold: (json['low_stock_threshold'] as num?)?.toInt() ?? 5,
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
      variants: (json['variants'] as List<dynamic>?)
              ?.map((e) => PosSyncVariant.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      inventoryModelVersion:
          (json['inventory_model_version'] as num?)?.toInt() ?? 0,
      posLayout: json['pos_layout'] as String? ?? 'grid_with_variant_picker',
    );

Map<String, dynamic> _$PosSyncResponseToJson(PosSyncResponse instance) =>
    <String, dynamic>{
      'branch_id': instance.branchId,
      'branch_name': instance.branchName,
      'branch_code': instance.branchCode,
      'branch_address': instance.branchAddress,
      'branch_phone': instance.branchPhone,
      'business_name': instance.businessName,
      'receipt_logo_base64': instance.receiptLogoBase64,
      'receipt_tagline': instance.receiptTagline,
      'receipt_thank_you': instance.receiptThankYou,
      'receipt_terms': instance.receiptTerms,
      'currency': instance.currency,
      'low_stock_threshold': instance.lowStockThreshold,
      'synced_at': instance.syncedAt.toIso8601String(),
      'categories': instance.categories.map((e) => e.toJson()).toList(),
      'products': instance.products.map((e) => e.toJson()).toList(),
      'tax_rates': instance.taxRates.map((e) => e.toJson()).toList(),
      'deals': instance.deals.map((e) => e.toJson()).toList(),
      'promotions': instance.promotions.map((e) => e.toJson()).toList(),
      'variants': instance.variants.map((e) => e.toJson()).toList(),
      'inventory_model_version': instance.inventoryModelVersion,
      'pos_layout': instance.posLayout,
    };
