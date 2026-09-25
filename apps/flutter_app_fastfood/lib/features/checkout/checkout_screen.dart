// features/checkout/checkout_screen.dart
//
// Take-payment screen. Reached from the cart overlay's "Take Payment" button.
//
// Flow:
//   pick a tender  →  (cash: enter amount + see change)  →  Complete Sale
//     → SaleRepository.submitSale(cartSnapshot, isOnline)
//         online  → store receipt, go to /pos/receipt/:id
//         queued  → toast "saved offline", go back to /pos
//
// The cart is cleared and the POS selection reset on success either way.

import 'package:decimal/decimal.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../providers/auth_notifier.dart';
import '../../providers/cart_notifier.dart';
import '../../providers/connectivity_provider.dart';
import '../../providers/currency_provider.dart';
import '../../providers/repository_providers.dart';
import '../../providers/session_notifier.dart';
import '../common/pill_button.dart';
import '../pos/pos_state.dart';
import '../pos/pos_theme.dart';
import '../sale/cart_service.dart';
import 'last_receipt_provider.dart';

// Must match core.payment_methods.PAYMENT_METHODS on the backend exactly —
// the server validates payment_method against that fixed list and rejects
// anything else (422).
const _tenders = <(String, IconData)>[
  ('Cash', Icons.payments_outlined),
  ('JazzCash', Icons.smartphone_outlined),
  ('EasyPaisa', Icons.account_balance_wallet_outlined),
  ('Online Transfer', Icons.account_balance_outlined),
  ('Credit Card', Icons.credit_card),
];

class CheckoutScreen extends ConsumerStatefulWidget {
  const CheckoutScreen({super.key});

  @override
  ConsumerState<CheckoutScreen> createState() => _CheckoutScreenState();
}

class _CheckoutScreenState extends ConsumerState<CheckoutScreen> {
  String _tender = 'Cash';
  String _entry = ''; // raw digits typed for a cash tender
  final _refCtrl = TextEditingController();
  final _keypadFocus = FocusNode(debugLabel: 'payment-keypad');
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _entry = ref.read(cartNotifierProvider).total.toString();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _keypadFocus.requestFocus();
    });
  }

  @override
  void dispose() {
    _refCtrl.dispose();
    _keypadFocus.dispose();
    super.dispose();
  }

  Decimal get _total => ref.read(cartNotifierProvider).total;

  Decimal get _tendered {
    if (_tender != 'Cash') return _total; // non-cash is always exact
    if (_entry.isEmpty) return Decimal.zero;
    return Decimal.tryParse(_entry) ?? Decimal.zero;
  }

  Decimal get _change {
    final c = _tendered - _total;
    return c > Decimal.zero ? c : Decimal.zero;
  }

  bool get _online => ref.read(connectivityProvider).valueOrNull ?? false;

  bool get _canComplete {
    if (_busy) return false;
    if (ref.read(cartNotifierProvider).items.isEmpty) return false;
    if (_tender == 'Cash') return _tendered >= _total;
    return true;
  }

  void _tapKey(String k) {
    setState(() {
      if (k == '⌫') {
        if (_entry.isNotEmpty) _entry = _entry.substring(0, _entry.length - 1);
      } else if (k == '.') {
        if (!_entry.contains('.')) _entry += _entry.isEmpty ? '0.' : '.';
      } else {
        final dot = _entry.indexOf('.');
        if (dot >= 0 && _entry.length - dot > 2) return; // max 2 decimals
        _entry += k;
      }
    });
  }

  void _handlePhysicalKey(KeyEvent event) {
    if (event is! KeyDownEvent || _tender != 'Cash' || _busy) return;
    if (event.logicalKey == LogicalKeyboardKey.backspace) {
      _tapKey('⌫');
      return;
    }
    if (event.logicalKey == LogicalKeyboardKey.enter ||
        event.logicalKey == LogicalKeyboardKey.numpadEnter) {
      _complete();
      return;
    }
    final character = event.character;
    if (character != null && RegExp(r'^[0-9.]$').hasMatch(character)) {
      _tapKey(character);
    }
  }

  Future<void> _complete() async {
    if (!_canComplete) return;
    final messenger = ScaffoldMessenger.of(context);
    final router = GoRouter.of(context);
    final cartNotifier = ref.read(cartNotifierProvider.notifier);
    final saleRepo = ref.read(saleRepositoryProvider);
    final online = _online;

    setState(() => _busy = true);

    // Attach exactly one tender to the cart. A fully-discounted (already $0)
    // cart is paid with an ordinary zero-amount tender — no special payment
    // method needed; the discount itself is applied earlier, in the cart
    // (cart_overlay.dart's "Apply Discount"), before checkout is ever reached.
    cartNotifier.clearPayments();
    cartNotifier.addPayment(CartPayment(
      paymentMethod: _tender,
      amount: _tender == 'Cash' ? _tendered : _total,
      reference: _refCtrl.text.trim().isEmpty ? null : _refCtrl.text.trim(),
    ));

    try {
      final snapshot = ref.read(cartNotifierProvider);
      final cashierName =
          ref.read(authNotifierProvider).valueOrNull?.cashierName;
      final cashierId = ref.read(authNotifierProvider).valueOrNull?.userId;
      final sessionId = ref.read(sessionNotifierProvider).valueOrNull?.id;
      final result = await saleRepo.submitSale(
        snapshot,
        isOnline: online,
        cashierName: cashierName,
        cashierId: cashierId,
        sessionId: sessionId,
      );
      if (!mounted) return;

      final receipt = result.receiptOrNull;
      cartNotifier.clear();
      ref.read(posNotifierProvider.notifier).resetAll();

      if (receipt != null) {
        ref.read(lastReceiptProvider.notifier).state = receipt;
        router.go('/pos/receipt/${receipt.saleId}');
      } else {
        messenger.showSnackBar(const SnackBar(
          content: Text('Sale saved offline — it will sync when back online.'),
        ));
        router.go('/pos');
      }
    } catch (e) {
      if (!mounted) return;
      setState(() => _busy = false);
      messenger.showSnackBar(SnackBar(
        content: Text('Could not complete the sale: $e'),
        backgroundColor: Colors.red.shade700,
      ));
    }
  }

  @override
  Widget build(BuildContext context) {
    final cart = ref.watch(cartNotifierProvider);
    final money = ref.watch(moneyProvider);

    return Scaffold(
      backgroundColor: PosTheme.bg,
      appBar: AppBar(
        backgroundColor: PosTheme.bg,
        elevation: 0,
        foregroundColor: PosTheme.text,
        title: const Text('Take Payment',
            style: TextStyle(fontWeight: FontWeight.w700)),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: _busy ? null : () => context.pop(),
        ),
      ),
      body: SafeArea(
        child: LayoutBuilder(builder: (context, constraints) {
          final compact = constraints.maxWidth < 700;
          final content = Flex(
            direction: compact ? Axis.vertical : Axis.horizontal,
            children: [
              Expanded(
                flex: 5,
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Amount due',
                          style: TextStyle(
                              color: PosTheme.textMuted, fontSize: 14)),
                      const SizedBox(height: 4),
                      Text(money(cart.total),
                          style: const TextStyle(
                              fontSize: 40,
                              fontWeight: FontWeight.w800,
                              color: PosTheme.text)),
                      const SizedBox(height: 24),
                      Wrap(
                        spacing: 10,
                        runSpacing: 10,
                        children: [
                          for (final (name, icon) in _tenders)
                            _TenderChip(
                              label: name,
                              icon: icon,
                              selected: _tender == name,
                              onTap: () => setState(() {
                                _tender = name;
                                if (name == 'Cash') {
                                  _entry = cart.total.toString();
                                  WidgetsBinding.instance.addPostFrameCallback(
                                      (_) => _keypadFocus.requestFocus());
                                }
                              }),
                            ),
                        ],
                      ),
                      const SizedBox(height: 24),
                      if (_tender == 'Cash') ...[
                        _Line('Tendered', money(_tendered)),
                        const SizedBox(height: 6),
                        _Line('Change', money(_change), highlight: true),
                        const SizedBox(height: 16),
                        Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: [
                            for (final v in _roundUps(cart.total))
                              _QuickCash(
                                label:
                                    money(v).replaceAll(RegExp(r'\.00$'), ''),
                                onTap: () =>
                                    setState(() => _entry = v.toString()),
                              ),
                          ],
                        ),
                      ] else ...[
                        TextField(
                          controller: _refCtrl,
                          decoration: InputDecoration(
                            labelText: 'Reference (optional)',
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                          ),
                        ),
                        const SizedBox(height: 12),
                        Text('Charged in full: ${money(cart.total)}',
                            style: const TextStyle(
                                color: PosTheme.textMuted, fontSize: 13)),
                      ],
                      const Spacer(),
                      if (!_online)
                        const Padding(
                          padding: EdgeInsets.only(bottom: 10),
                          child: Text(
                              'Offline — the sale is queued and syncs later.',
                              style: TextStyle(
                                  color: PosTheme.textMuted, fontSize: 12)),
                        ),
                      PillButton(
                        label: 'Complete Sale',
                        loading: _busy,
                        onTap: _canComplete ? _complete : null,
                      ),
                    ],
                  ),
                ),
              ),
              if (_tender == 'Cash')
                Container(
                  width: compact ? double.infinity : 320,
                  height: compact ? 330 : null,
                  color: PosTheme.surface,
                  padding: const EdgeInsets.all(20),
                  child: KeyboardListener(
                    focusNode: _keypadFocus,
                    autofocus: true,
                    onKeyEvent: _handlePhysicalKey,
                    child: _Keypad(onKey: _tapKey),
                  ),
                ),
            ],
          );
          return compact
              ? SingleChildScrollView(
                  child: SizedBox(height: 1050, child: content))
              : content;
        }),
      ),
    );
  }

  /// A couple of convenient "round up" cash amounts above the total.
  List<Decimal> _roundUps(Decimal total) {
    final t = total.toDouble();
    final out = <int>[];
    for (final step in const [10, 50, 100, 500, 1000]) {
      final up = (t / step).ceil() * step;
      if (up > t && !out.contains(up)) out.add(up);
      if (out.length == 3) break;
    }
    return out.map(Decimal.fromInt).toList();
  }
}

// ── small widgets ───────────────────────────────────────────────────────────

class _TenderChip extends StatelessWidget {
  final String label;
  final IconData icon;
  final bool selected;
  final VoidCallback onTap;
  const _TenderChip({
    required this.label,
    required this.icon,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 120),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: selected ? PosTheme.accentLight : PosTheme.surface,
          borderRadius: PosTheme.pillRadius,
          border: Border.all(
            color: selected ? PosTheme.accent : PosTheme.divider,
            width: selected ? 2 : 1,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon,
                size: 18,
                color: selected ? PosTheme.accentText : PosTheme.textMuted),
            const SizedBox(width: 8),
            Text(label,
                style: TextStyle(
                  fontWeight: FontWeight.w600,
                  color: selected ? PosTheme.accentText : PosTheme.text,
                )),
          ],
        ),
      ),
    );
  }
}

class _Line extends StatelessWidget {
  final String label;
  final String value;
  final bool highlight;
  const _Line(this.label, this.value, {this.highlight = false});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label,
            style: const TextStyle(color: PosTheme.textMuted, fontSize: 15)),
        Text(value,
            style: TextStyle(
              fontSize: highlight ? 22 : 15,
              fontWeight: highlight ? FontWeight.w800 : FontWeight.w600,
              color: highlight ? PosTheme.accent2 : PosTheme.text,
            )),
      ],
    );
  }
}

class _QuickCash extends StatelessWidget {
  final String label;
  final VoidCallback onTap;
  const _QuickCash({required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return OutlinedButton(
      onPressed: onTap,
      style: OutlinedButton.styleFrom(
        foregroundColor: PosTheme.text,
        side: const BorderSide(color: PosTheme.divider),
        shape: const StadiumBorder(),
      ),
      child: Text(label),
    );
  }
}

class _Keypad extends StatelessWidget {
  final void Function(String) onKey;
  const _Keypad({required this.onKey});

  @override
  Widget build(BuildContext context) {
    const keys = [
      '1', '2', '3', //
      '4', '5', '6',
      '7', '8', '9',
      '.', '0', '⌫',
    ];
    return GridView.count(
      crossAxisCount: 3,
      mainAxisSpacing: 12,
      crossAxisSpacing: 12,
      childAspectRatio: 1.4,
      children: [
        for (final k in keys)
          GestureDetector(
            onTap: () {
              HapticFeedback.selectionClick();
              onKey(k);
            },
            child: Container(
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                boxShadow: PosTheme.shadowSm,
              ),
              alignment: Alignment.center,
              child: Text(k,
                  style: const TextStyle(
                      fontSize: 22, fontWeight: FontWeight.w700)),
            ),
          ),
      ],
    );
  }
}
