import 'package:fastfood_pos/core/network/dio_client.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('catalog, heartbeat, and staff routes use the device token', () {
    for (final path in [
      '/api/v1/pos/auth/cashier',
      '/api/v1/pos/auth/staff',
      '/api/v1/pos/auth/staff-pin',
      '/api/v1/pos/sync/full',
      '/api/v1/pos/sync/delta?since=2026-01-01T00:00:00Z',
      '/api/v1/pos/device/heartbeat',
      '/api/v1/pos/attendance/staff',
      '/api/v1/pos/attendance/punch',
      '/api/v1/pos/attendance/status',
    ]) {
      expect(usesDeviceTokenForPath(path), isTrue, reason: path);
    }
  });

  test('sale, shift, and offline upload routes use the cashier token', () {
    for (final path in [
      '/api/v1/pos/sales/',
      '/api/v1/pos/session/open',
      '/api/v1/pos/session/close',
      '/api/v1/pos/sync/upload',
    ]) {
      expect(usesDeviceTokenForPath(path), isFalse, reason: path);
    }
  });
}
