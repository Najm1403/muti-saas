import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fastfood_pos/db/app_database.dart';

LocalSalesTableCompanion _sale({
  required String id,
  required DateTime soldAt,
  required bool synced,
  required String cashierId,
  required String sessionId,
}) =>
    LocalSalesTableCompanion.insert(
      id: id,
      saleNumber: '$id-number',
      soldAt: soldAt,
      subtotal: '10.00',
      discount: '0.00',
      total: '10.00',
      taxAmount: '0.00',
      synced: Value(synced),
      cashierId: Value(cashierId),
      sessionId: Value(sessionId),
    );

void main() {
  late AppDatabase db;

  setUp(() => db = AppDatabase.forTesting(NativeDatabase.memory()));
  tearDown(() => db.close());

  test('local report filters use date, cashier, and shift', () async {
    final now = DateTime.utc(2026, 9, 20, 12);
    await db.saleDao.insertSaleWithItems(
      sale: _sale(
        id: 'matching',
        soldAt: now,
        synced: true,
        cashierId: 'cashier-a',
        sessionId: 'shift-a',
      ),
      items: const [],
      itemOptions: const [],
      payments: const [],
    );
    await db.saleDao.insertSaleWithItems(
      sale: _sale(
        id: 'other-shift',
        soldAt: now,
        synced: true,
        cashierId: 'cashier-a',
        sessionId: 'shift-b',
      ),
      items: const [],
      itemOptions: const [],
      payments: const [],
    );

    final rows = await db.saleDao.recentSales(
      dateFrom: DateTime.utc(2026, 9, 20),
      dateTo: DateTime.utc(2026, 9, 20, 23, 59, 59),
      cashierId: 'cashier-a',
      sessionId: 'shift-a',
    );

    expect(rows.map((row) => row.id), ['matching']);
  });

  test('90-day cleanup never removes an unsynced sale', () async {
    final now = DateTime.utc(2026, 9, 20);
    for (final entry in [
      ('old-synced', now.subtract(const Duration(days: 100)), true),
      ('old-unsynced', now.subtract(const Duration(days: 100)), false),
      ('recent-synced', now.subtract(const Duration(days: 10)), true),
    ]) {
      await db.saleDao.insertSaleWithItems(
        sale: _sale(
          id: entry.$1,
          soldAt: entry.$2,
          synced: entry.$3,
          cashierId: 'cashier-a',
          sessionId: 'shift-a',
        ),
        items: const [],
        itemOptions: const [],
        payments: const [],
      );
    }

    expect(
      await db.saleDao.pruneSyncedOlderThan(
        now.subtract(const Duration(days: 90)),
      ),
      1,
    );
    expect(
      (await db.saleDao.recentSales()).map((row) => row.id).toSet(),
      {'old-unsynced', 'recent-synced'},
    );
  });
}
