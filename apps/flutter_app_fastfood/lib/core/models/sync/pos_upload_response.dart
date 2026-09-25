import 'package:json_annotation/json_annotation.dart';
import 'pos_upload_result.dart';

part 'pos_upload_response.g.dart';

/// Summary returned by POST /sync/upload after a batch offline upload.
///
/// [total] equals [created] + [duplicates] + [errors]. The tablet uses
/// [results] to determine which local sale IDs to mark as synced —
/// both "created" and "duplicate" outcomes are considered successfully synced.
@JsonSerializable(explicitToJson: true)
class PosUploadResponse {
  /// Total number of sales in the uploaded batch.
  final int total;

  /// Sales accepted and created on the server.
  final int created;

  /// Sales already present on the server (idempotent re-upload); safe to mark synced.
  final int duplicates;

  /// Sales rejected due to validation or server errors.
  final int errors;

  /// Per-sale outcome list matching the order of the upload batch.
  final List<PosUploadResult> results;

  const PosUploadResponse({
    required this.total,
    required this.created,
    required this.duplicates,
    required this.errors,
    this.results = const [],
  });

  /// Constructs from the JSON body returned by POST /sync/upload.
  factory PosUploadResponse.fromJson(Map<String, dynamic> json) =>
      _$PosUploadResponseFromJson(json);

  Map<String, dynamic> toJson() => _$PosUploadResponseToJson(this);
}
