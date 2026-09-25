import 'dart:io';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../core/network/dio_client.dart';

part 'connectivity_provider.g.dart';

/// Whether the configured API can be attempted with the current interfaces.
///
/// A loopback API (`localhost`, `127.0.0.1`, or `::1`) remains usable without
/// public internet. A remote HTTP(S) API follows Wi-Fi/mobile/ethernet state.
bool hasApiConnectivity(
  List<ConnectivityResult> results, {
  String apiUrl = apiBaseUrl,
}) {
  final host = Uri.tryParse(apiUrl)?.host;
  final address = host == null ? null : InternetAddress.tryParse(host);
  if (host == 'localhost' || address?.isLoopback == true) return true;
  return results.any((result) => result != ConnectivityResult.none);
}

/// Emits an initial value immediately, then follows interface changes.
/// keepAlive ensures the subscription survives widget rebuilds.
@Riverpod(keepAlive: true)
Stream<bool> connectivity(ConnectivityRef ref) async* {
  final service = Connectivity();
  yield hasApiConnectivity(await service.checkConnectivity());
  await for (final results in service.onConnectivityChanged) {
    yield hasApiConnectivity(results);
  }
}
