// Renders the activation screen in isolation (no platform plugins needed).

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fastfood_pos/features/activation/activation_screen.dart';

void main() {
  testWidgets('activation screen shows the code prompt', (tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: MaterialApp(home: ActivationScreen()),
      ),
    );

    expect(find.text('Activate this POS'), findsOneWidget);
    expect(find.text('STORIXX'), findsOneWidget);
    expect(find.bySemanticsLabel('Storixx logo'), findsOneWidget);
    expect(find.text('ACTIVATION CODE'), findsOneWidget);
    expect(find.widgetWithText(GestureDetector, 'Activate'), findsWidgets);
  });
}
