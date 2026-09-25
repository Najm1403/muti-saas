import 'package:decimal/decimal.dart';
import 'package:drift/native.dart';
import 'package:fastfood_pos/db/app_database.dart';
import 'package:fastfood_pos/providers/database_provider.dart';
import 'package:fastfood_pos/providers/auth_notifier.dart';
import 'package:fastfood_pos/providers/currency_provider.dart';
import 'package:fastfood_pos/providers/discount_eligibility_provider.dart';
import 'package:fastfood_pos/providers/menu_provider.dart';
import 'package:fastfood_pos/providers/repository_providers.dart';
import 'package:fastfood_pos/features/pos/pos_state.dart';
import 'package:fastfood_pos/features/pos/widgets/cart_overlay.dart';
import 'package:fastfood_pos/features/sale/cart_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

/// Replaces the old "Free Guest" tender-chip visibility test now that
/// [checkout_screen.dart] no longer special-cases discounting — the cashier
/// applies a manual discount from the cart panel instead (see
/// cart_overlay.dart's "Apply Discount" button), gated by
/// [discountEligibilityProvider] (backend: `sales.discount` permission).
class _FakeAuthNotifier extends AuthNotifier {
  @override
  Future<AuthState> build() async => const AuthState(
        isDeviceActivated: true,
        isCashierLoggedIn: true,
        tenantId: 't1',
        branchId: 'b1',
        deviceId: 'd1',
        userId: 'u1',
      );
}

CartService _cartWithOneTenDollarItem() => CartService()
  ..addItem(CartItem(
    id: 'item-1',
    variantId: 'variant-1',
    productId: 'product-1',
    productName: 'Test Burger',
    unitPrice: Decimal.parse('10.00'),
    quantity: Decimal.one,
  ));

void main() {
  for (final size in [const Size(1400, 1000), const Size(390, 844)]) {
    for (final permitted in [false, true]) {
      testWidgets(
          'Apply Discount visibility for permission=$permitted width=${size.width}',
          (tester) async {
        final db = AppDatabase.forTesting(NativeDatabase.memory());
        addTearDown(db.close);
        tester.view.physicalSize = size;
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);

        await tester.pumpWidget(ProviderScope(overrides: [
          appDatabaseProvider.overrideWithValue(db),
          cartServiceProvider.overrideWithValue(_cartWithOneTenDollarItem()),
          defaultTaxRateProvider.overrideWith((ref) async => null),
          discountPermissionProvider.overrideWith(
              (ref) async => DiscountPermission(eligible: permitted)),
          authNotifierProvider.overrideWith(() => _FakeAuthNotifier()),
          currencyProvider.overrideWithValue('Rs.'),
        ], child: const MaterialApp(home: Scaffold(body: CartOverlay()))));
        await tester.pump();

        final container =
            ProviderScope.containerOf(tester.element(find.byType(CartOverlay)));
        container.read(posNotifierProvider.notifier).openCart();
        await tester.pumpAndSettle();

        expect(find.text('Offers and deals'), findsOneWidget);
        expect(find.text('Apply Discount'), permitted ? findsOneWidget : findsNothing);

        if (permitted) {
          await tester.tap(find.text('Apply Discount'));
          await tester.pumpAndSettle();
          expect(find.text('Apply Discount'), findsWidgets);
          expect(find.text('New total: Rs. 10.00'), findsOneWidget);

          await tester.enterText(find.byType(TextField), '25');
          await tester.pumpAndSettle();
          expect(find.text('New total: Rs. 7.50'), findsOneWidget);

          await tester.tap(find.widgetWithText(FilledButton, 'Apply'));
          await tester.pumpAndSettle();

          expect(find.text('Discount'), findsOneWidget);
          expect(find.text('-Rs. 2.50'), findsOneWidget);
        }
      });
    }
  }

  testWidgets('Discount is clamped to the cashier\'s max_discount_percent cap',
      (tester) async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);

    await tester.pumpWidget(ProviderScope(overrides: [
      appDatabaseProvider.overrideWithValue(db),
      cartServiceProvider.overrideWithValue(_cartWithOneTenDollarItem()),
      defaultTaxRateProvider.overrideWith((ref) async => null),
      discountPermissionProvider.overrideWith((ref) async =>
          DiscountPermission(eligible: true, maxPercent: Decimal.parse('10'))),
      authNotifierProvider.overrideWith(() => _FakeAuthNotifier()),
      currencyProvider.overrideWithValue('Rs.'),
    ], child: const MaterialApp(home: Scaffold(body: CartOverlay()))));
    await tester.pump();

    final container =
        ProviderScope.containerOf(tester.element(find.byType(CartOverlay)));
    container.read(posNotifierProvider.notifier).openCart();
    await tester.pumpAndSettle();

    await tester.tap(find.text('Apply Discount'));
    await tester.pumpAndSettle();

    expect(find.text('Your maximum: 10% (Rs. 1.00)'), findsOneWidget);

    // Cashier tries to give 25% — above their 10% ceiling.
    await tester.enterText(find.byType(TextField), '25');
    await tester.pumpAndSettle();
    expect(find.text('Capped at your maximum discount.'), findsOneWidget);
    expect(find.text('New total: Rs. 9.00'), findsOneWidget);

    await tester.tap(find.widgetWithText(FilledButton, 'Apply'));
    await tester.pumpAndSettle();

    expect(find.text('-Rs. 1.00'), findsOneWidget);
  });
}
