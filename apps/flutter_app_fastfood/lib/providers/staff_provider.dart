import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../core/models/auth/staff_member.dart';
import 'repository_providers.dart';

part 'staff_provider.g.dart';

/// Active staff for this device's branch — powers the staff-picker grid.
///
/// Requires a device token (onboarding complete). Invalidate to refresh after
/// a sync or when returning to the staff screen.
@riverpod
Future<List<StaffMember>> staffList(StaffListRef ref) =>
    ref.watch(authRepositoryProvider).listStaff();
