import 'package:dio/dio.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../core/network/dio_client.dart';
import '../core/security/token_storage.dart';

part 'dio_provider.g.dart';

/// Singleton token storage — survives for the lifetime of the app.
///
/// device_token is read from encrypted storage; cashier_token is in-memory only.
@Riverpod(keepAlive: true)
TokenStorage tokenStorage(TokenStorageRef ref) => TokenStorage();

/// Holds a device lifecycle failure code, or null when the device is operating
/// normally. Set by the Dio interceptor and handled by the app shell.
@Riverpod(keepAlive: true)
class DeviceLock extends _$DeviceLock {
  @override
  String? build() => null;

  void set(String code) => state = code;
  void clear() => state = null;
}

/// Singleton Dio instance with token injection and error normalization
/// interceptors already attached. keepAlive so interceptors are not recreated.
@Riverpod(keepAlive: true)
Dio dio(DioRef ref) => buildDio(
      ref.watch(tokenStorageProvider),
      onDeviceLock: (code) => ref.read(deviceLockProvider.notifier).set(code),
    );
