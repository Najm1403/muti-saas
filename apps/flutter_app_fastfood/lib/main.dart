import 'dart:io' show Platform;

import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app.dart';
import 'services/sync_service.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  // The POS UI is landscape-only on mobile; on desktop the OS window is freely
  // resizable so orientation locking does not apply.
  if (!kIsWeb && (Platform.isAndroid || Platform.isIOS)) {
    SystemChrome.setPreferredOrientations(const [
      DeviceOrientation.landscapeLeft,
      DeviceOrientation.landscapeRight,
    ]);
  }
  runApp(const ProviderScope(child: _Root()));
}

/// Top-level widget that bootstraps the provider graph before handing off to
/// the app shell. Watching [syncServiceProvider] here ensures the background
/// sync timer and connectivity listener start as soon as the app launches —
/// without this watch the provider stays dormant until something else reads it.
class _Root extends ConsumerWidget {
  const _Root();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.watch(syncServiceProvider); // start background sync
    return const FastFoodPosApp();
  }
}
