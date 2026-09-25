// A sale the server rejects for a deterministic reason used to retry
// forever — every periodic sync tick and every reconnect resubmitted it and
// hit the identical error again (see SyncService._uploadPending and
// SaleDao.markNeedsReview). These tests pin the local-DB half of that fix:
// a quarantined sale drops out of SaleDao.unsynced() (so it's never
// resubmitted) but stays visible via SaleDao.needsReviewSales() (so the sync
// banner can keep reporting it).
import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fastfood_pos/db/app_database.dart';

LocalSalesTableCompanion _sale(String id) => LocalSalesTableCompanion.insert(
      id: id,
      saleNumber: '$id-number',
      soldAt: DateTime.utc(2026, 9, 22, 12),
      subtotal: '10.00',
      discount: '0.00',
      total: '10.00',
      taxAmount: '0.00',
      synced: const Value(false),
    );

void main() {
  late AppDatabase db;

  setUp(() => db = AppDatabase.forTesting(NativeDatabase.memory()));
  tearDown(() => db.close());

  test('a fresh unsynced sale is retryable and not yet flagged for review',
      () async {
    await db.saleDao.insertSaleWithItems(
      sale: _sale('s1'),
      items: const [],
      itemOptions: const [],
      payments: const [],
    );

    expect((await db.saleDao.unsynced()).map((s) => s.id), ['s1']);
    expect(await db.saleDao.needsReviewSales(), isEmpty);
  });

  test('markNeedsReview quarantines a sale out of the retry queue', () async {
    await db.saleDao.insertSaleWithItems(
      sale: _sale('bad-sale'),
      items: const [],
      itemOptions: const [],
      payments: const [],
    );

    await db.saleDao.markNeedsReview('bad-sale', 'component pairing rejected');

    // No longer resubmitted on the next sync tick...
    expect(await db.saleDao.unsynced(), isEmpty);
    // ...but still reported so the cashier/admin isn't left in the dark.
    final review = await db.saleDao.needsReviewSales();
    expect(review.map((s) => s.id), ['bad-sale']);
    expect(review.single.syncError, 'component pairing rejected');
  });

  test('quarantining one sale does not affect other unsynced sales',
      () async {
    await db.saleDao.insertSaleWithItems(
      sale: _sale('bad-sale'),
      items: const [],
      itemOptions: const [],
      payments: const [],
    );
    await db.saleDao.insertSaleWithItems(
      sale: _sale('good-sale'),
      items: const [],
      itemOptions: const [],
      payments: const [],
    );

    await db.saleDao.markNeedsReview('bad-sale', 'deterministic rejection');

    expect((await db.saleDao.unsynced()).map((s) => s.id), ['good-sale']);
  });
}
