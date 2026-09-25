import 'package:flutter_test/flutter_test.dart';

import 'package:fastfood_pos/features/pos/pos_state.dart';

void main() {
  test('untyped empty selection maps are normalized without a runtime cast',
      () {
    final state = const PosState().copyWith(
      selectedVariantOptions: {},
      selectedAddons: {},
      selectedComponents: {},
    );

    expect(state.selectedVariantOptions, isA<Map<String, String>>());
    expect(state.selectedComponents, isA<Map<String, String>>());
    expect(state.selectedAddons, isA<Map<String, Set<String>>>());
    expect(state.selectedVariantOptions, isEmpty);
    expect(state.selectedComponents, isEmpty);
  });
}
