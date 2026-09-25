import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../features/attendance/attendance_repository.dart';
import '../features/auth/auth_repository.dart';
import '../features/sale/cart_service.dart';
import '../features/sale/sale_repository.dart';
import '../features/session/session_repository.dart';
import '../features/sync/menu_repository.dart';
import '../features/sync/sync_repository.dart';
import 'api_providers.dart';
import 'auth_notifier.dart';
import 'database_provider.dart';
import 'dio_provider.dart';

part 'repository_providers.g.dart';

/// Handles device activation and cashier login; persists tokens to [TokenStorage].
@Riverpod(keepAlive: true)
AuthRepository authRepository(AuthRepositoryRef ref) => AuthRepository(
      ref.watch(posAuthApiProvider),
      ref.watch(tokenStorageProvider),
    );

/// Orchestrates full/delta catalog sync and offline sale upload.
@Riverpod(keepAlive: true)
SyncRepository syncRepository(SyncRepositoryRef ref) => SyncRepository(
      ref.watch(posSyncApiProvider),
      ref.watch(appDatabaseProvider),
    );

/// Read-only access to the local catalog tables (categories, products, etc.).
@Riverpod(keepAlive: true)
MenuRepository menuRepository(MenuRepositoryRef ref) =>
    MenuRepository(ref.watch(appDatabaseProvider));

/// Submits sales online or queues them locally when offline.
@Riverpod(keepAlive: true)
SaleRepository saleRepository(SaleRepositoryRef ref) => SaleRepository(
      ref.watch(posSaleApiProvider),
      ref.watch(appDatabaseProvider),
      ref.watch(tokenStorageProvider),
    );

/// Manages cashier shift open/close/current via the session API.
@Riverpod(keepAlive: true)
SessionRepository sessionRepository(SessionRepositoryRef ref) =>
    SessionRepository(ref.watch(posSessionApiProvider));

/// Attendance clock-in/out — device token only, no cashier session involved.
@Riverpod(keepAlive: true)
AttendanceRepository attendanceRepository(AttendanceRepositoryRef ref) =>
    AttendanceRepository(ref.watch(posAttendanceApiProvider));

/// In-memory cart — keepAlive so the cart survives widget rebuilds.
@Riverpod(keepAlive: true)
CartService cartService(CartServiceRef ref) {
  ref.watch(authNotifierProvider.select((state) => (state.valueOrNull?.userId, state.valueOrNull?.branchId)));
  return CartService();
}
