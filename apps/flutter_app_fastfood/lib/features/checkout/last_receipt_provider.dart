// features/checkout/last_receipt_provider.dart
//
// Hands the freshly-created server receipt from CheckoutScreen to ReceiptScreen
// (go_router only carries the sale id in the path). Cleared on "New Order".

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models/sale/pos_receipt_response.dart';

/// The receipt from the most recently completed online sale, or null.
final lastReceiptProvider = StateProvider<PosReceiptResponse?>((ref) => null);
