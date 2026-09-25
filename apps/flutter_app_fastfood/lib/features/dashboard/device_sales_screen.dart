import 'package:decimal/decimal.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models/sale/pos_receipt_response.dart';
import '../../core/network/api_exception.dart';
import '../../providers/currency_provider.dart';
import '../../providers/repository_providers.dart';
import '../pos/pos_theme.dart';

/// Cloud-backed recent transactions for this cashier/device. A completed bill
/// from the current open shift can be cancelled in full; older bills belong in
/// the Sales Return workflow.
class DeviceSalesScreen extends ConsumerStatefulWidget {
  const DeviceSalesScreen({super.key, this.report = false});
  final bool report;

  @override
  ConsumerState<DeviceSalesScreen> createState() => _DeviceSalesScreenState();
}

class _DeviceSalesScreenState extends ConsumerState<DeviceSalesScreen> {
  late Future<List<PosReceiptResponse>> _sales;
  // Populates the cashier/shift dropdown option lists — date-scoped only
  // (never by cashier/session), so picking one filter never shrinks the
  // other dropdown's available options down to just the current selection.
  late Future<List<PosReceiptResponse>> _pickerSource;
  String? _busyId;
  DateTime? _dateFrom;
  DateTime? _dateTo;
  String? _cashierId;
  String? _sessionId;

  @override
  void initState() {
    super.initState();
    _reload();
  }

  // Filters must reach the query itself, not just post-filter the already
  // fetched, limit-capped list — otherwise a "From date" outside the most
  // recent `limit` sales silently returns an incomplete/empty result with
  // no indication data is missing.
  void _reload() {
    final repo = ref.read(saleRepositoryProvider);
    _sales = repo.recentSales(
      limit: widget.report ? 1000 : 50,
      dateFrom: _dateFrom,
      dateTo: _dateTo,
      cashierId: _cashierId,
      sessionId: _sessionId,
    );
    _pickerSource = repo.recentSales(
      limit: widget.report ? 1000 : 50,
      dateFrom: _dateFrom,
      dateTo: _dateTo,
    );
  }

  Future<void> _pickDate({required bool from}) async {
    final picked = await showDatePicker(
      context: context,
      initialDate: (from ? _dateFrom : _dateTo) ?? DateTime.now(),
      firstDate: DateTime.now().subtract(const Duration(days: 365 * 3)),
      lastDate: DateTime.now(),
    );
    if (picked == null || !mounted) return;
    setState(() {
      if (from) {
        _dateFrom = DateTime(picked.year, picked.month, picked.day);
      } else {
        _dateTo =
            DateTime(picked.year, picked.month, picked.day, 23, 59, 59, 999);
      }
      _reload();
    });
  }

  String _dateLabel(DateTime? value, String fallback) => value == null
      ? fallback
      : '${value.year}-${value.month.toString().padLeft(2, '0')}-${value.day.toString().padLeft(2, '0')}';

  Future<void> _cancel(PosReceiptResponse sale) async {
    final controller = TextEditingController();
    final reason = await showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Cancel Order / Bill'),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          Text('Cancel ${sale.saleNumber} for the full amount '
              '${sale.currency} ${sale.total}?'),
          const SizedBox(height: 14),
          TextField(
            controller: controller,
            autofocus: true,
            maxLength: 500,
            decoration: const InputDecoration(
              labelText: 'Reason (required)',
              hintText: 'For example: duplicate bill',
              border: OutlineInputBorder(),
            ),
          ),
          const Text(
            'This keeps an audit record and restores tracked stock.',
            style: TextStyle(fontSize: 12, color: PosTheme.textMuted),
          ),
        ]),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(dialogContext),
              child: const Text('Keep bill')),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: Colors.red.shade700),
            onPressed: () {
              final value = controller.text.trim();
              if (value.isNotEmpty) Navigator.pop(dialogContext, value);
            },
            child: const Text('Cancel entire bill'),
          ),
        ],
      ),
    );
    controller.dispose();
    if (reason == null || !mounted) return;
    setState(() => _busyId = sale.saleId);
    try {
      final result = await ref
          .read(saleRepositoryProvider)
          .cancelSale(sale.saleId, reason);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(
            'Bill cancelled. Reversal ${result['refund_number']} recorded.'),
        backgroundColor: Colors.green.shade700,
      ));
      setState(_reload);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text('Could not cancel bill: $e'),
            backgroundColor: Colors.red.shade700));
      }
    } finally {
      if (mounted) setState(() => _busyId = null);
    }
  }

  @override
  Widget build(BuildContext context) {
    final money = ref.watch(moneyProvider);
    return Scaffold(
      backgroundColor: PosTheme.bg,
      appBar: AppBar(
          title: Text(
              widget.report ? 'Recent sales report' : 'Recent transactions')),
      body: FutureBuilder<List<PosReceiptResponse>>(
        future: _sales,
        builder: (context, snapshot) {
          if (snapshot.hasError) {
            final error = snapshot.error;
            return Center(
                child: Text('Could not load sales: '
                    '${error is ApiException ? error.message : error}'));
          }
          if (!snapshot.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          // Already server/local-DAO filtered by _reload(); re-applying the
          // same predicates here is a harmless no-op safety net, not the
          // actual filter (that would silently miss data past `limit`).
          final sales = snapshot.data!.where((sale) {
            if (_dateFrom != null && sale.soldAt.isBefore(_dateFrom!)) {
              return false;
            }
            if (_dateTo != null && sale.soldAt.isAfter(_dateTo!)) return false;
            if (_cashierId != null && sale.userId != _cashierId) return false;
            if (_sessionId != null && sale.sessionId != _sessionId) {
              return false;
            }
            return true;
          }).toList();
          final completed =
              sales.where((s) => s.status == 'COMPLETED').toList();
          final total = completed.fold<Decimal>(
              Decimal.zero,
              (sum, sale) =>
                  sum + (Decimal.tryParse(sale.total) ?? Decimal.zero));
          return RefreshIndicator(
            onRefresh: () async {
              setState(_reload);
              await _sales;
            },
            child: ListView(padding: const EdgeInsets.all(16), children: [
              if (widget.report)
                FutureBuilder<List<PosReceiptResponse>>(
                  future: _pickerSource,
                  builder: (context, pickerSnap) {
                    // Options come from a date-only-filtered fetch, never
                    // narrowed by the currently selected cashier/shift, so
                    // picking one filter never hides the other's choices.
                    final pickerSales = pickerSnap.data ?? const [];
                    final cashierNames = <String, String>{
                      for (final sale in pickerSales)
                        if (sale.userId != null)
                          sale.userId!: sale.cashierName.isEmpty
                              ? 'Unknown cashier'
                              : sale.cashierName,
                    };
                    final shiftIds = pickerSales
                        .map((sale) => sale.sessionId)
                        .whereType<String>()
                        .toSet()
                        .toList();
                    return Card(
                      child: Padding(
                        padding: const EdgeInsets.all(12),
                        child: Wrap(
                          spacing: 10,
                          runSpacing: 10,
                          crossAxisAlignment: WrapCrossAlignment.center,
                          children: [
                            OutlinedButton.icon(
                              onPressed: () => _pickDate(from: true),
                              icon: const Icon(Icons.date_range, size: 18),
                              label: Text(_dateLabel(_dateFrom, 'From date')),
                            ),
                            OutlinedButton.icon(
                              onPressed: () => _pickDate(from: false),
                              icon: const Icon(Icons.event, size: 18),
                              label: Text(_dateLabel(_dateTo, 'To date')),
                            ),
                            DropdownButton<String>(
                              value: _cashierId ?? '',
                              hint: const Text('All cashiers'),
                              items: [
                                const DropdownMenuItem<String>(
                                    value: '', child: Text('All cashiers')),
                                ...cashierNames.entries.map((entry) =>
                                    DropdownMenuItem<String>(
                                        value: entry.key,
                                        child: Text(entry.value))),
                              ],
                              onChanged: (value) => setState(() {
                                _cashierId =
                                    value?.isEmpty == true ? null : value;
                                _reload();
                              }),
                            ),
                            DropdownButton<String>(
                              value: _sessionId ?? '',
                              hint: const Text('All shifts'),
                              items: [
                                const DropdownMenuItem<String>(
                                    value: '', child: Text('All shifts')),
                                ...shiftIds.map((id) => DropdownMenuItem<String>(
                                    value: id,
                                    child: Text('Shift ${id.substring(0, 8)}'))),
                              ],
                              onChanged: (value) => setState(() {
                                _sessionId =
                                    value?.isEmpty == true ? null : value;
                                _reload();
                              }),
                            ),
                            TextButton(
                              onPressed: () => setState(() {
                                _dateFrom = null;
                                _dateTo = null;
                                _cashierId = null;
                                _sessionId = null;
                                _reload();
                              }),
                              child: const Text('Clear filters'),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              if (widget.report)
                Card(
                    child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(children: [
                    Expanded(
                        child:
                            Text('${completed.length} completed recent sales')),
                    Text(money(total),
                        style: const TextStyle(fontWeight: FontWeight.bold)),
                  ]),
                )),
              if (sales.isEmpty)
                const Padding(
                    padding: EdgeInsets.all(24),
                    child:
                        Center(child: Text('No recent sales on this device.'))),
              for (final sale in sales)
                Card(
                    child: Padding(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                  child: Row(children: [
                    Expanded(
                        child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                          Text(sale.saleNumber,
                              style:
                                  const TextStyle(fontWeight: FontWeight.w700)),
                          const SizedBox(height: 3),
                          Text('${sale.soldAt.toLocal()} · ${sale.status}',
                              style: const TextStyle(
                                  fontSize: 12, color: PosTheme.textMuted)),
                        ])),
                    Text(money(Decimal.tryParse(sale.total) ?? Decimal.zero)),
                    if (!widget.report && sale.status == 'COMPLETED') ...[
                      const SizedBox(width: 12),
                      OutlinedButton.icon(
                        onPressed: _busyId == null ? () => _cancel(sale) : null,
                        icon: _busyId == sale.saleId
                            ? const SizedBox(
                                width: 14,
                                height: 14,
                                child:
                                    CircularProgressIndicator(strokeWidth: 2))
                            : const Icon(Icons.cancel_outlined, size: 17),
                        label: const Text('Cancel bill'),
                        style: OutlinedButton.styleFrom(
                            foregroundColor: Colors.red.shade700),
                      ),
                    ],
                  ]),
                )),
            ]),
          );
        },
      ),
    );
  }
}
