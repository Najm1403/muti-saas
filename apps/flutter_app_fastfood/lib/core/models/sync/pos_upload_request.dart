import 'package:json_annotation/json_annotation.dart';
import 'pos_offline_sale.dart';

part 'pos_upload_request.g.dart';

/// Batch upload payload sent to POST /sync/upload.
///
/// All unsynced sales are collected from the local DB and sent in a single
/// request to minimize round-trips. The server processes each sale
/// independently and returns a per-sale result in [PosUploadResponse].
@JsonSerializable(explicitToJson: true)
class PosUploadRequest {
  final List<PosOfflineSale> sales;

  const PosUploadRequest({required this.sales});

  /// Constructs from JSON (symmetric factory, rarely used client-side).
  factory PosUploadRequest.fromJson(Map<String, dynamic> json) =>
      _$PosUploadRequestFromJson(json);

  Map<String, dynamic> toJson() => _$PosUploadRequestToJson(this);
}
