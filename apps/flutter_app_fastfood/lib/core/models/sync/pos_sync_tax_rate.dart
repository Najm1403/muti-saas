import 'package:json_annotation/json_annotation.dart';

part 'pos_sync_tax_rate.g.dart';

/// A tax rate configuration synced from the cloud.
///
/// [rate] is a String (Decimal, e.g. "0.15" for 15%). [isInclusive] determines
/// whether the rate is already baked into product prices or added on top.
/// Only the rate where [isDefault] is true is applied automatically at checkout.
@JsonSerializable()
class PosSyncTaxRate {
  final String id;
  final String name;

  /// Decimal rate value, e.g. "0.10" for 10%. Stored as String to avoid float drift.
  final String rate;

  /// True when the tax is included in [basePrice] rather than added at checkout.
  @JsonKey(name: 'is_inclusive')
  final bool isInclusive;

  @JsonKey(name: 'is_default')
  final bool isDefault;

  const PosSyncTaxRate({
    required this.id,
    required this.name,
    required this.rate,
    required this.isInclusive,
    required this.isDefault,
  });

  /// Constructs from the JSON array item in [PosSyncResponse.taxRates].
  factory PosSyncTaxRate.fromJson(Map<String, dynamic> json) =>
      _$PosSyncTaxRateFromJson(json);

  Map<String, dynamic> toJson() => _$PosSyncTaxRateToJson(this);
}
