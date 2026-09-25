import 'package:json_annotation/json_annotation.dart';
import 'pos_sync_category.dart';
import 'pos_sync_product.dart';
import 'pos_sync_tax_rate.dart';
import 'pos_sync_deal.dart';
import 'pos_sync_promotion.dart';
import 'pos_sync_variant.dart';

part 'pos_sync_response.g.dart';

/// Complete catalog payload returned by GET /sync/full.
///
/// Used on first launch (or after a forced re-sync) to populate the entire
/// local Drift database from scratch. All lists default to empty so partial
/// catalogs (branches with no deals, for example) deserialize without error.
@JsonSerializable(explicitToJson: true)
class PosSyncResponse {
  @JsonKey(name: 'branch_id')
  final String branchId;

  @JsonKey(name: 'branch_name')
  final String branchName;

  @JsonKey(name: 'branch_code')
  final String branchCode;
  @JsonKey(name: 'branch_address')
  final String? branchAddress;
  @JsonKey(name: 'branch_phone')
  final String? branchPhone;
  @JsonKey(name: 'business_name')
  final String businessName;
  @JsonKey(name: 'receipt_logo_base64')
  final String? receiptLogoBase64;
  @JsonKey(name: 'receipt_tagline')
  final String? receiptTagline;
  @JsonKey(name: 'receipt_thank_you')
  final String? receiptThankYou;
  @JsonKey(name: 'receipt_terms')
  final String? receiptTerms;

  /// Shop money display string (e.g. "Rs."). Persisted to `app_settings`
  /// so every screen can format amounts even while offline.
  @JsonKey(defaultValue: 'Rs.')
  final String currency;
  @JsonKey(name: 'low_stock_threshold', defaultValue: 5)
  final int lowStockThreshold;

  /// Server-side timestamp written to [AppSettingsTable] as `last_sync_at`
  /// so the next delta sync can use it as the `since` cursor.
  @JsonKey(name: 'synced_at')
  final DateTime syncedAt;

  final List<PosSyncCategory> categories;
  final List<PosSyncProduct> products;

  @JsonKey(name: 'tax_rates')
  final List<PosSyncTaxRate> taxRates;

  final List<PosSyncDeal> deals;
  final List<PosSyncPromotion> promotions;

  /// Composed, sellable Variant rows for every product (spec D1/D2/D3).
  final List<PosSyncVariant> variants;

  @JsonKey(name: 'inventory_model_version')
  final int inventoryModelVersion;

  /// Business-Template-driven POS layout (spec Part C / F3/G4) —
  /// 'grid_with_variant_picker' or 'grid_quick_tap'. Unknown/missing values
  /// must fall back to the side-panel layout, never crash.
  @JsonKey(name: 'pos_layout', defaultValue: 'grid_with_variant_picker')
  final String posLayout;

  const PosSyncResponse({
    required this.branchId,
    required this.branchName,
    required this.branchCode,
    this.branchAddress,
    this.branchPhone,
    required this.businessName,
    this.receiptLogoBase64,
    this.receiptTagline,
    this.receiptThankYou,
    this.receiptTerms,
    this.currency = 'Rs.',
    this.lowStockThreshold = 5,
    required this.syncedAt,
    this.categories = const [],
    this.products = const [],
    this.taxRates = const [],
    this.deals = const [],
    this.promotions = const [],
    this.variants = const [],
    this.inventoryModelVersion = 0,
    this.posLayout = 'grid_with_variant_picker',
  });

  /// Constructs from the JSON body returned by GET /sync/full.
  factory PosSyncResponse.fromJson(Map<String, dynamic> json) =>
      _$PosSyncResponseFromJson(json);

  /// [explicitToJson] required so nested lists are fully serialized.
  Map<String, dynamic> toJson() => _$PosSyncResponseToJson(this);
}
