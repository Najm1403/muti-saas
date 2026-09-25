import 'package:json_annotation/json_annotation.dart';

part 'pos_upload_result.g.dart';

/// Per-sale outcome within a [PosUploadResponse].
///
/// The server processes each sale independently so one failure does not
/// block others. Check [status] before treating [saleId] as valid.
@JsonSerializable()
class PosUploadResult {
  @JsonKey(name: 'sale_number')
  final String saleNumber;

  /// Server-assigned sale ID on success; null when status is "error".
  @JsonKey(name: 'sale_id')
  final String? saleId;

  /// "created" — new sale accepted.
  /// "duplicate" — sale_number already exists; safe to mark synced locally.
  /// "error" — server rejected the sale; see [error] for details.
  final String status;

  final String? error;

  /// Only meaningful when [status] is "error". True (default) means the
  /// device should keep retrying this sale on future sync ticks; false means
  /// the server rejected it for a deterministic reason (bad/inconsistent
  /// data, a genuine conflict) that retrying will never fix — see
  /// [SyncService] for how this is used to quarantine a sale instead of
  /// resubmitting it forever.
  @JsonKey(name: 'retryable', defaultValue: true)
  final bool retryable;

  const PosUploadResult({
    required this.saleNumber,
    this.saleId,
    required this.status,
    this.error,
    this.retryable = true,
  });

  /// Constructs from the JSON array item in [PosUploadResponse.results].
  factory PosUploadResult.fromJson(Map<String, dynamic> json) =>
      _$PosUploadResultFromJson(json);

  Map<String, dynamic> toJson() => _$PosUploadResultToJson(this);
}
