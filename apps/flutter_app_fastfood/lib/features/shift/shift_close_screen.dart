// features/shift/shift_close_screen.dart
//
// Loads the live shift reconciliation, takes a counted-cash figure, shows the
// variance, and closes the shift.

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/models/session/session_summary_response.dart';
import '../../core/network/api_exception.dart';
import '../../providers/auth_notifier.dart';
import '../../providers/currency_provider.dart';
import '../../providers/session_notifier.dart';
import '../../services/pdf_service.dart';
import '../common/pill_button.dart';
import '../pos/pos_theme.dart';

class ShiftCloseScreen extends ConsumerStatefulWidget {
  const ShiftCloseScreen({super.key});

  @override
  ConsumerState<ShiftCloseScreen> createState() => _ShiftCloseScreenState();
}

class _ShiftCloseScreenState extends ConsumerState<ShiftCloseScreen> {
  final _pdf = PdfService();
  late Future<SessionSummaryResponse> _future;
  final _counted = TextEditingController();
  bool _closing = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _future = ref.read(sessionNotifierProvider.notifier).summary();
  }

  @override
  void dispose() {
    _counted.dispose();
    super.dispose();
  }

  double _num(String s) => double.tryParse(s) ?? 0;

  Future<void> _close() async {
    setState(() {
      _closing = true;
      _error = null;
    });
    try {
      final res = await ref.read(sessionNotifierProvider.notifier).closeSession(
            closingCash:
                _counted.text.trim().isEmpty ? '0.00' : _counted.text.trim(),
          );
      if (!mounted) return;
      final v = _num(res.variance);
      // Unconditional: closing a shift always signs the cashier out and
      // lands on the staff picker, so any cashier can open the next shift —
      // no branch that leaves the device signed in as whoever just closed
      // out (that used to be reachable via a "View Details" option here,
      // which — unless the cashier remembered to tap a small Log out icon
      // on the screen it led to, rather than just navigating away — left
      // the device signed in as them, silently falling through to "open a
      // new shift" as themselves instead of the cashier list). The full
      // breakdown is already visible on this screen both before and after
      // closing, and remains reviewable later via Dashboard → Shift History
      // once any cashier is signed back in, so nothing is lost.
      await showDialog<void>(
        context: context,
        builder: (_) => AlertDialog(
          title: const Text('Shift closed'),
          content: Text(
            v == 0
                ? 'Drawer balanced.'
                : v > 0
                    ? 'Over by ${ref.read(moneyProvider)(v)}.'
                    : 'Short by ${ref.read(moneyProvider)(v.abs())}.',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Done'),
            ),
          ],
        ),
      );
      if (!mounted) return;
      ref.read(authNotifierProvider.notifier).cashierLogout();
      context.go('/staff');
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) setState(() => _error = 'Could not reach the server');
    } finally {
      if (mounted) setState(() => _closing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final money = ref.watch(moneyProvider);
    final currency = ref.watch(currencyProvider);

    return Scaffold(
      backgroundColor: PosTheme.bg,
      appBar: AppBar(
        backgroundColor: PosTheme.bg,
        elevation: 0,
        foregroundColor: PosTheme.text,
        title: const Text('Close shift'),
      ),
      body: FutureBuilder<SessionSummaryResponse>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const Center(
                child: CircularProgressIndicator(color: PosTheme.accent));
          }
          if (snap.hasError) {
            return Center(
              child: Text(
                snap.error is ApiException
                    ? (snap.error as ApiException).message
                    : 'Could not load the shift summary',
                style: const TextStyle(color: PosTheme.textMuted),
              ),
            );
          }
          final s = snap.data!.summary;
          final session = snap.data!.session;
          final counted = _num(_counted.text);
          final expected = _num(s.expectedCash);
          final variance = counted - expected;

          return Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 480),
              child: ListView(
                padding: const EdgeInsets.all(24),
                children: [
                  if (session.shiftNumber != null)
                    _row('Shift', session.shiftNumber!, bold: true),
                  _row('Opening cash', money(s.openingCash)),
                  _row('Completed sales', '${s.salesCount}'),
                  _row('Subtotal / gross sales', money(s.subtotalTotal)),
                  _row('Discounts', '-${money(s.discountTotal)}'),
                  _row('Tax', money(s.taxTotal)),
                  _row('Sales total', money(s.grossTotal), bold: true),
                  const Divider(height: 28),
                  const Text('PAYMENTS RECEIVED',
                      style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          color: PosTheme.accentText)),
                  for (final e in s.byPaymentMethod.entries)
                    _row(e.key, money(e.value)),
                  _row('All payments', money(s.totalPayments), bold: true),
                  const Divider(height: 28),
                  _row('Refunds', '${s.refundsCount}'),
                  for (final e in s.refundsByPaymentMethod.entries)
                    if (_num(e.value) != 0)
                      _row('${e.key} refunds', '-${money(e.value)}'),
                  _row('All refunds', '-${money(s.refundTotal)}', bold: true),
                  _row('Cancelled bills', '${s.cancellationsCount}'),
                  for (final e in s.cancellationsByPaymentMethod.entries)
                    if (_num(e.value) != 0)
                      _row('${e.key} cancellations', money(e.value)),
                  _row('Cancelled bill total', money(s.cancellationTotal),
                      bold: true),
                  _row('Net sales after refunds', money(s.netTotal),
                      bold: true),
                  const Divider(height: 28),
                  _row('Expected cash', money(s.expectedCash), bold: true),
                  const SizedBox(height: 20),
                  const Text('Counted cash in drawer',
                      style:
                          TextStyle(fontSize: 13, color: PosTheme.textMuted)),
                  const SizedBox(height: 8),
                  TextField(
                    controller: _counted,
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                    inputFormatters: [
                      FilteringTextInputFormatter.allow(RegExp(r'[0-9.]')),
                    ],
                    onChanged: (_) => setState(() {}),
                    style: const TextStyle(
                        fontSize: 22, fontWeight: FontWeight.w700),
                    decoration: InputDecoration(
                      prefixText: '$currency ',
                      filled: true,
                      fillColor: PosTheme.surface,
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(16),
                        borderSide: BorderSide.none,
                      ),
                      contentPadding: const EdgeInsets.symmetric(
                          horizontal: 16, vertical: 16),
                    ),
                  ),
                  const SizedBox(height: 12),
                  if (_counted.text.trim().isNotEmpty)
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 14, vertical: 10),
                      decoration: BoxDecoration(
                        color: variance == 0
                            ? PosTheme.accent2Light
                            : const Color(0xFFFDECEA),
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: Text(
                        variance == 0
                            ? 'Balanced'
                            : variance > 0
                                ? 'Over by ${money(variance)}'
                                : 'Short by ${money(variance.abs())}',
                        style: TextStyle(
                          fontWeight: FontWeight.w700,
                          color: variance == 0
                              ? PosTheme.accent2Text
                              : const Color(0xFFC62828),
                        ),
                      ),
                    ),
                  if (_error != null) ...[
                    const SizedBox(height: 10),
                    Text(_error!,
                        style: const TextStyle(
                            color: Color(0xFFD84315), fontSize: 13)),
                  ],
                  const SizedBox(height: 20),
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: () => _pdf.printShiftSummary(snap.data!),
                          icon: const Icon(Icons.print_outlined),
                          label: const Text('Print'),
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: () => _pdf.shareShiftSummary(snap.data!),
                          icon: const Icon(Icons.picture_as_pdf_outlined),
                          label: const Text('Save PDF'),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  PillButton(
                    label: 'Close shift',
                    loading: _closing,
                    onTap: _close,
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _row(String label, String value, {bool bold = false}) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 6),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label,
                style: TextStyle(
                  fontSize: 14,
                  color: bold ? PosTheme.text : PosTheme.textMuted,
                  fontWeight: bold ? FontWeight.w700 : FontWeight.w500,
                )),
            Text(value,
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: bold ? FontWeight.w800 : FontWeight.w600,
                  color: PosTheme.text,
                )),
          ],
        ),
      );
}
