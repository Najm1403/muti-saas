import 'package:json_annotation/json_annotation.dart';
import 'pos_sync_category.dart';
import 'pos_sync_product.dart';
import 'pos_sync_tax_rate.dart';
import 'pos_sync_deal.dart';
import 'pos_sync_promotion.dart';

part 'pos_delta_sync_response.g.dart';

/// Incremental catalog changes returned by GET /sync/delta?since=<timestamp>.
///
/// Only records modified after [since] are included. The tablet upserts them
/// into the local DB â€” unchanged records are untouched. [syncedAt] becomes
/// the new `last_sync_at` cursor for the next delta cycle.
@JsonSerializable(explicitToJson: true)
class PosDeltaSyncResponse {
  @JsonKey(name: 'branch_id')
  final String branchId;

  /// The `since` timestamp echoed back by the server for audit/debug purposes.
  final DateTime since;

  /// New cursor to store as `last_sync_at` after applying this delta.
  @JsonKey(name: 'synced_at')
  final DateTime syncedAt;

  final List<PosSyncCategory> categories;
  final List<PosSyncProduct> products;

  @JsonKey(name: 'tax_rates')
  final List<PosSyncTaxRate> taxRates;

  final List<PosSyncDeal> deals;
  final List<PosSyncPromotion> promotions;

  const PosDeltaSyncResponse({
    required this.branchId,
    required this.since,
    required this.syncedAt,
    this.categories = const [],
    this.products = const [],
    this.taxRates = const [],
    this.deals = const [],
    this.promotions = const [],
  });

  /// Constructs from the JSON body returned by GET /sync/delta.
  factory PosDeltaSyncResponse.fromJson(Map<String, dynamic> json) =>
      _$PosDeltaSyncResponseFromJson(json);

  Map<String, dynamic> toJson() => _$PosDeltaSyncResponseToJson(this);
}
