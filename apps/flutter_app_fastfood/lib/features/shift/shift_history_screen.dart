// features/shift/shift_history_screen.dart
//
// This cashier's past (closed) shifts — the "day book" view. Reachable from
// the dashboard at any time, including after a shift has been closed and
// its one-time close-screen summary is otherwise gone for good.

import 'package:decimal/decimal.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/models/session/session_response.dart';
import '../../core/models/session/session_summary_response.dart';
import '../../core/network/api_exception.dart';
import '../../providers/auth_notifier.dart';
import '../../providers/currency_provider.dart';
import '../../providers/repository_providers.dart';
import '../../providers/session_notifier.dart';
import '../../services/pdf_service.dart';
import '../pos/pos_theme.dart';

/// Signs the cashier out and returns to the staff grid. Shown on both
/// shift-history screens as a general "done browsing, hand off the device"
/// affordance — e.g. a cashier reviewing past shifts here between shifts
/// (no session, still signed in — see app.dart's redirect exemption) has a
/// clear way to finish instead of silently falling through to "open a new
/// shift" as themselves on back-navigation. (Closing a shift itself always
/// signs out and returns here directly — see shift_close_screen.dart.)
class _LogoutAction extends ConsumerWidget {
  const _LogoutAction();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final hasOpenShift = ref.watch(sessionNotifierProvider).valueOrNull != null;
    return IconButton(
      tooltip: 'Log out',
      icon: const Icon(Icons.logout),
      onPressed: () {
        ref.read(authNotifierProvider.notifier).cashierLogout();
        context.go('/staff');
      },
      // Only shown as a strong affordance when there's no open shift to
      // return to — mid-shift, the normal Dashboard "Log out" action covers it.
      color: hasOpenShift ? PosTheme.textMuted : PosTheme.text,
    );
  }
}

class ShiftHistoryScreen extends ConsumerStatefulWidget {
  const ShiftHistoryScreen({super.key});

  @override
  ConsumerState<ShiftHistoryScreen> createState() => _ShiftHistoryScreenState();
}

class _ShiftHistoryScreenState extends ConsumerState<ShiftHistoryScreen> {
  late Future<List<SessionResponse>> _history;

  @override
  void initState() {
    super.initState();
    _reload();
  }

  void _reload() {
    _history = ref.read(sessionRepositoryProvider).history();
  }

  @override
  Widget build(BuildContext context) {
    final money = ref.watch(moneyProvider);
    return Scaffold(
      backgroundColor: PosTheme.bg,
      appBar: AppBar(
        title: const Text('Shift history'),
        actions: const [_LogoutAction()],
      ),
      body: FutureBuilder<List<SessionResponse>>(
        future: _history,
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
                    : 'Could not load shift history',
                style: const TextStyle(color: PosTheme.textMuted),
              ),
            );
          }
          final sessions = snap.data!;
          if (sessions.isEmpty) {
            return const Center(
              child: Text(
                'No closed shifts yet',
                style: TextStyle(color: PosTheme.textMuted, fontSize: 14),
              ),
            );
          }
          return RefreshIndicator(
            onRefresh: () async {
              setState(_reload);
              await _history;
            },
            child: ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: sessions.length,
              separatorBuilder: (_, __) => const SizedBox(height: 10),
              itemBuilder: (context, i) {
                final s = sessions[i];
                final closingCash = s.closingCash == null
                    ? null
                    : Decimal.tryParse(s.closingCash!);
                return _ShiftTile(
                  session: s,
                  money: money,
                  closingCash: closingCash,
                  onTap: () => context.push('/shift-history/${s.id}'),
                );
              },
            ),
          );
        },
      ),
    );
  }
}

class _ShiftTile extends StatelessWidget {
  final SessionResponse session;
  final String Function(Decimal) money;
  final Decimal? closingCash;
  final VoidCallback onTap;

  const _ShiftTile({
    required this.session,
    required this.money,
    required this.closingCash,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final opened = session.openedAt.toLocal();
    final closed = session.closedAt?.toLocal();
    final dateLabel =
        '${opened.year}-${opened.month.toString().padLeft(2, '0')}-${opened.day.toString().padLeft(2, '0')}';
    final timeLabel = closed == null
        ? TimeOfDay.fromDateTime(opened).format(context)
        : '${TimeOfDay.fromDateTime(opened).format(context)} – ${TimeOfDay.fromDateTime(closed).format(context)}';
    // Older shifts (opened before this field existed) fall back to the date
    // as the primary line, same as before.
    final hasShiftNumber = session.shiftNumber != null;
    final primaryLabel = hasShiftNumber ? 'Shift ${session.shiftNumber}' : dateLabel;
    final secondaryLabel = hasShiftNumber ? '$dateLabel · $timeLabel' : timeLabel;

    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: PosTheme.surface,
          borderRadius: BorderRadius.circular(16),
        ),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(primaryLabel,
                      style: const TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w700,
                          color: PosTheme.text)),
                  const SizedBox(height: 2),
                  Text(secondaryLabel,
                      style: const TextStyle(
                          fontSize: 12, color: PosTheme.textMuted)),
                ],
              ),
            ),
            if (closingCash != null)
              Text(money(closingCash!),
                  style: const TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w700,
                      color: PosTheme.text)),
            const SizedBox(width: 8),
            const Icon(Icons.chevron_right, color: PosTheme.textMuted),
          ],
        ),
      ),
    );
  }
}

// ── Detail: one past shift's full reconciliation ────────────────────────────

class ShiftHistoryDetailScreen extends ConsumerWidget {
  final String sessionId;
  const ShiftHistoryDetailScreen({super.key, required this.sessionId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final money = ref.watch(moneyProvider);
    return Scaffold(
      backgroundColor: PosTheme.bg,
      appBar: AppBar(
        title: const Text('Shift summary'),
        actions: const [_LogoutAction()],
      ),
      body: FutureBuilder<SessionSummaryResponse>(
        future: ref.read(sessionRepositoryProvider).historySummary(sessionId),
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
                    : 'Could not load this shift',
                style: const TextStyle(color: PosTheme.textMuted),
              ),
            );
          }
          final session = snap.data!.session;
          final s = snap.data!.summary;
          final closingCash = session.closingCash == null
              ? null
              : Decimal.tryParse(session.closingCash!) ?? Decimal.zero;
          final expected = Decimal.tryParse(s.expectedCash) ?? Decimal.zero;
          final variance = closingCash == null ? null : closingCash - expected;

          return Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 480),
              child: ListView(
                padding: const EdgeInsets.all(24),
                children: [
                  if (session.shiftNumber != null)
                    _row('Shift', session.shiftNumber!, bold: true),
                  _row('Opened', session.openedAt.toLocal().toString()),
                  if (session.closedAt != null)
                    _row('Closed', session.closedAt!.toLocal().toString()),
                  const Divider(height: 28),
                  _row('Opening cash', money(s.openingCash)),
                  _row('Completed sales', '${s.salesCount}'),
                  _row('Subtotal / gross sales', money(s.subtotalTotal)),
                  _row('Discounts', '-${money(s.discountTotal)}'),
                  _row('Tax', money(s.taxTotal)),
                  _row('Sales total', money(s.grossTotal), bold: true),
                  const Divider(height: 28),
                  for (final e in s.byPaymentMethod.entries)
                    _row(e.key, money(e.value)),
                  _row('All payments', money(s.totalPayments), bold: true),
                  const Divider(height: 28),
                  _row('Refunds', '${s.refundsCount}'),
                  for (final e in s.refundsByPaymentMethod.entries)
                    if ((double.tryParse(e.value) ?? 0) != 0)
                      _row('${e.key} refunds', '-${money(e.value)}'),
                  _row('All refunds', '-${money(s.refundTotal)}', bold: true),
                  _row('Cancelled bills', '${s.cancellationsCount}'),
                  for (final e in s.cancellationsByPaymentMethod.entries)
                    if ((double.tryParse(e.value) ?? 0) != 0)
                      _row('${e.key} cancellations', money(e.value)),
                  _row('Cancelled bill total', money(s.cancellationTotal),
                      bold: true),
                  _row('Net sales after refunds', money(s.netTotal),
                      bold: true),
                  const Divider(height: 28),
                  _row('Expected cash', money(s.expectedCash), bold: true),
                  if (closingCash != null)
                    _row('Counted cash', money(closingCash), bold: true),
                  if (variance != null) ...[
                    const SizedBox(height: 16),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 14, vertical: 10),
                      decoration: BoxDecoration(
                        color: variance == Decimal.zero
                            ? PosTheme.accent2Light
                            : const Color(0xFFFDECEA),
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: Text(
                        variance == Decimal.zero
                            ? 'Balanced'
                            : variance > Decimal.zero
                                ? 'Over by ${money(variance)}'
                                : 'Short by ${money(-variance)}',
                        style: TextStyle(
                          fontWeight: FontWeight.w700,
                          color: variance == Decimal.zero
                              ? PosTheme.accent2Text
                              : const Color(0xFFC62828),
                        ),
                      ),
                    ),
                  ],
                  const SizedBox(height: 20),
                  Row(children: [
                    Expanded(
                        child: OutlinedButton.icon(
                      onPressed: () =>
                          PdfService().printShiftSummary(snap.data!),
                      icon: const Icon(Icons.print_outlined),
                      label: const Text('Print'),
                    )),
                    const SizedBox(width: 10),
                    Expanded(
                        child: OutlinedButton.icon(
                      onPressed: () =>
                          PdfService().shareShiftSummary(snap.data!),
                      icon: const Icon(Icons.picture_as_pdf_outlined),
                      label: const Text('Save PDF'),
                    )),
                  ]),
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
            Expanded(
              child: Text(label,
                  style: TextStyle(
                    fontSize: 14,
                    color: bold ? PosTheme.text : PosTheme.textMuted,
                    fontWeight: bold ? FontWeight.w700 : FontWeight.w500,
                  )),
            ),
            Text(value,
                textAlign: TextAlign.right,
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: bold ? FontWeight.w800 : FontWeight.w600,
                  color: PosTheme.text,
                )),
          ],
        ),
      );
}
