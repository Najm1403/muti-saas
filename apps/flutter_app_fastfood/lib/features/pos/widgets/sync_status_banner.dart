import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../providers/database_provider.dart';
import '../../../services/sync_service.dart';

class SyncStatusBanner extends ConsumerWidget {
  const SyncStatusBanner({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) => StreamBuilder<String?>(
      stream:
          ref.watch(appDatabaseProvider).settingsDao.watchValue('sync_error'),
      builder: (context, snapshot) {
        final error = snapshot.data;
        if (error == null || error.isEmpty) return const SizedBox.shrink();
        return Material(
            color: Colors.amber.shade100,
            child: ListTile(
                dense: true,
                title: const Text('Sync needs attention'),
                onTap: () => showDialog(
                    context: context,
                    builder: (context) => AlertDialog(
                            title: const Text('Sync details'),
                            content: SingleChildScrollView(
                                child: SelectableText(error)),
                            actions: [
                              TextButton(
                                  onPressed: () => Navigator.pop(context),
                                  child: const Text('Close'))
                            ])),
                trailing: TextButton(
                    onPressed: () => ref.read(syncServiceProvider).retryNow(),
                    child: const Text('Retry'))));
      });
}
