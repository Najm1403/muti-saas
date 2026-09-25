import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../core/api/pos_attendance_api.dart';
import '../core/api/pos_auth_api.dart';
import '../core/api/pos_device_api.dart';
import '../core/api/pos_sale_api.dart';
import '../core/api/pos_session_api.dart';
import '../core/api/pos_sync_api.dart';
import 'dio_provider.dart';

part 'api_providers.g.dart';

/// Thin HTTP client for device activation and cashier login.
@Riverpod(keepAlive: true)
PosAuthApi posAuthApi(PosAuthApiRef ref) =>
    PosAuthApi(ref.watch(dioProvider));

/// Thin HTTP client for full/delta sync and offline sale upload.
@Riverpod(keepAlive: true)
PosSyncApi posSyncApi(PosSyncApiRef ref) =>
    PosSyncApi(ref.watch(dioProvider));

/// Thin HTTP client for online sale creation and receipt fetch.
@Riverpod(keepAlive: true)
PosSaleApi posSaleApi(PosSaleApiRef ref) =>
    PosSaleApi(ref.watch(dioProvider));

/// Thin HTTP client for cashier session open/close/current.
@Riverpod(keepAlive: true)
PosSessionApi posSessionApi(PosSessionApiRef ref) =>
    PosSessionApi(ref.watch(dioProvider));

/// Thin HTTP client for the device heartbeat endpoint.
@Riverpod(keepAlive: true)
PosDeviceApi posDeviceApi(PosDeviceApiRef ref) =>
    PosDeviceApi(ref.watch(dioProvider));

/// Thin HTTP client for attendance clock-in/out (device token only).
@Riverpod(keepAlive: true)
PosAttendanceApi posAttendanceApi(PosAttendanceApiRef ref) =>
    PosAttendanceApi(ref.watch(dioProvider));
