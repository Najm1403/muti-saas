import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models/sale/pos_receipt_item.dart';
import '../../core/models/sale/pos_receipt_response.dart';
import '../../providers/repository_providers.dart';
import '../pos/pos_theme.dart';

class SalesReturnScreen extends ConsumerStatefulWidget {
  const SalesReturnScreen({super.key});
  @override
  ConsumerState<SalesReturnScreen> createState() => _SalesReturnScreenState();
}

class _SalesReturnScreenState extends ConsumerState<SalesReturnScreen> {
  final _invoice = TextEditingController();
  final _reason = TextEditingController();
  PosReceiptResponse? _sale;
  final Map<String, int> _quantities = {};
  bool _loading = false;
  bool _submitting = false;

  // Today's sales, shown by default below the lookup box so the cashier
  // can browse/tap instead of always needing the exact Invoice ID — see
  // _loadTodaySales(). Filtering as the cashier types is purely client-side
  // against this already-fetched list (no per-keystroke API calls); the
  // "Look up" button/Enter still does a real server lookup by exact number,
  // for an older invoice from before today that isn't in this list.
  List<PosReceiptResponse> _todaySales = [];
  bool _loadingToday = true;
  String? _todayError;
  String _filterText = '';

  @override
  void initState() {
    super.initState();
    _invoice.addListener(() {
      if (mounted) setState(() => _filterText = _invoice.text.trim());
    });
    _loadTodaySales();
  }

  @override
  void dispose() {
    _invoice.dispose();
    _reason.dispose();
    super.dispose();
  }

  int _remaining(PosReceiptItem item) {
    final purchased = double.tryParse(item.quantity) ?? 0;
    final returned = double.tryParse(item.returnedQuantity) ?? 0;
    return math.max(0, (purchased - returned).floor());
  }

  Future<void> _loadTodaySales() async {
    setState(() {
      _loadingToday = true;
      _todayError = null;
    });
    final now = DateTime.now();
    try {
      final sales = await ref.read(saleRepositoryProvider).recentSales(
            limit: 200,
            dateFrom: DateTime(now.year, now.month, now.day),
            dateTo: DateTime(now.year, now.month, now.day, 23, 59, 59, 999),
          );
      if (mounted) setState(() => _todaySales = sales);
    } catch (e) {
      if (mounted) setState(() => _todayError = "Could not load today's sales: $e");
    } finally {
      if (mounted) setState(() => _loadingToday = false);
    }
  }

  List<PosReceiptResponse> get _filteredTodaySales {
    if (_filterText.isEmpty) return _todaySales;
    final needle = _filterText.toLowerCase();
    return _todaySales
        .where((s) =>
            s.saleNumber.toLowerCase().contains(needle) ||
            s.cashierName.toLowerCase().contains(needle))
        .toList();
  }

  Future<void> _lookup([String? number]) async {
    final target = (number ?? _invoice.text).trim();
    if (target.isEmpty) return;
    setState(() {
      _loading = true;
      _sale = null;
      _quantities.clear();
    });
    try {
      final sale =
          await ref.read(saleRepositoryProvider).getReceiptByNumber(target);
      if (mounted) setState(() => _sale = sale);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text('Invoice lookup failed: $e'),
            backgroundColor: Colors.red.shade700));
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _backToList() {
    setState(() {
      _sale = null;
      _quantities.clear();
      _invoice.clear();
    });
  }

  Future<void> _submit() async {
    final sale = _sale;
    if (sale == null) return;
    final selected =
        sale.items.where((i) => (_quantities[i.id] ?? 0) > 0).toList();
    if (selected.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Select at least one returned item.')));
      return;
    }
    final confirmed = await showDialog<bool>(
        context: context,
        builder: (dialogContext) => AlertDialog(
              title: const Text('Confirm Sales Return'),
              content: Text(
                  'Return ${selected.length} selected line(s) from ${sale.saleNumber}? '
                  'The refund is calculated from the original bill.'),
              actions: [
                TextButton(
                    onPressed: () => Navigator.pop(dialogContext, false),
                    child: const Text('Back')),
                FilledButton(
                    onPressed: () => Navigator.pop(dialogContext, true),
                    child: const Text('Complete return')),
              ],
            ));
    if (confirmed != true || !mounted) return;
    setState(() => _submitting = true);
    try {
      final result = await ref.read(saleRepositoryProvider).returnItems(
            sale.saleId,
            selected
                .map((i) =>
                    {'sale_item_id': i.id, 'quantity': _quantities[i.id]})
                .toList(),
            _reason.text,
          );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text('Return completed: ${result['refund_number']} · '
            '${sale.currency} ${result['amount']}'),
        backgroundColor: Colors.green.shade700,
      ));
      _reason.clear();
      await _lookup(sale.saleNumber);
      unawaited(_loadTodaySales());
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text('Could not complete return: $e'),
            backgroundColor: Colors.red.shade700));
      }
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final sale = _sale;
    return Scaffold(
      backgroundColor: PosTheme.bg,
      appBar: AppBar(title: const Text('Sales Return')),
      body: ListView(padding: const EdgeInsets.all(20), children: [
        const Text('Find an invoice',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
        const SizedBox(height: 6),
        const Text(
            "Type to filter today's sales below, or enter the exact Invoice ID "
            'and press Enter / Look up for an older invoice.',
            style: TextStyle(color: PosTheme.textMuted)),
        const SizedBox(height: 14),
        Row(children: [
          Expanded(
              child: TextField(
            controller: _invoice,
            autofocus: true,
            textInputAction: TextInputAction.search,
            onSubmitted: (_) => _lookup(),
            decoration: const InputDecoration(
                labelText: 'Invoice ID or filter',
                border: OutlineInputBorder()),
          )),
          const SizedBox(width: 12),
          FilledButton.icon(
            onPressed: _loading ? null : () => _lookup(),
            icon: _loading
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.search),
            label: const Text('Look up'),
          ),
        ]),
        if (sale == null) ...[
          const SizedBox(height: 20),
          Row(children: [
            const Text("Today's sales",
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
            const Spacer(),
            IconButton(
              onPressed: _loadingToday ? null : _loadTodaySales,
              icon: const Icon(Icons.refresh),
              tooltip: 'Refresh',
            ),
          ]),
          if (_loadingToday)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 24),
              child: Center(child: CircularProgressIndicator()),
            )
          else if (_todayError != null)
            Card(
                color: const Color(0xFFFFF1F2),
                child: Padding(
                    padding: const EdgeInsets.all(14),
                    child: Text(_todayError!,
                        style: TextStyle(color: Colors.red.shade700))))
          else if (_filteredTodaySales.isEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 24),
              child: Center(
                child: Text(
                  _filterText.isEmpty
                      ? 'No sales yet today.'
                      : 'No sales match "$_filterText".',
                  style: const TextStyle(color: PosTheme.textMuted),
                ),
              ),
            )
          else
            for (final s in _filteredTodaySales)
              _TodaySaleTile(
                sale: s,
                loading: _loading,
                onTap: () => _lookup(s.saleNumber),
              ),
        ],
        if (sale != null) ...[
          const SizedBox(height: 20),
          TextButton.icon(
            onPressed: _submitting ? null : _backToList,
            icon: const Icon(Icons.arrow_back),
            label: const Text("Back to today's sales"),
          ),
          const SizedBox(height: 8),
          Card(
              child: Padding(
            padding: const EdgeInsets.all(16),
            child:
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                Expanded(
                    child: Text(sale.saleNumber,
                        style: const TextStyle(
                            fontSize: 18, fontWeight: FontWeight.w800))),
                Text('${sale.currency} ${sale.total}',
                    style: const TextStyle(fontWeight: FontWeight.w700)),
              ]),
              Text(
                  '${sale.soldAt.toLocal()} · ${sale.cashierName} · ${sale.status}',
                  style:
                      const TextStyle(color: PosTheme.textMuted, fontSize: 12)),
            ]),
          )),
          if (sale.status != 'COMPLETED')
            const Card(
                color: Color(0xFFFFF1F2),
                child: Padding(
                    padding: EdgeInsets.all(14),
                    child: Text(
                        'This invoice is cancelled or already fully returned.'))),
          const SizedBox(height: 10),
          for (final item in sale.items)
            _ReturnLine(
              item: item,
              remaining: _remaining(item),
              selected: _quantities[item.id] ?? 0,
              onChanged: sale.status == 'COMPLETED' && item.id != null
                  ? (value) => setState(() => _quantities[item.id!] = value)
                  : null,
            ),
          const SizedBox(height: 12),
          TextField(
            controller: _reason,
            maxLength: 500,
            decoration: const InputDecoration(
                labelText: 'Return reason (optional)',
                border: OutlineInputBorder()),
          ),
          FilledButton.icon(
            onPressed:
                _submitting || sale.status != 'COMPLETED' ? null : _submit,
            icon: _submitting
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.assignment_return_outlined),
            label: const Text('Complete Sales Return'),
          ),
        ],
      ]),
    );
  }
}

class _TodaySaleTile extends StatelessWidget {
  const _TodaySaleTile(
      {required this.sale, required this.loading, required this.onTap});
  final PosReceiptResponse sale;
  final bool loading;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final completed = sale.status == 'COMPLETED';
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        onTap: loading ? null : onTap,
        title: Text(sale.saleNumber,
            style: const TextStyle(fontWeight: FontWeight.w700)),
        subtitle: Text(
            '${_time(sale.soldAt)} · ${sale.cashierName}',
            style: const TextStyle(color: PosTheme.textMuted, fontSize: 12)),
        trailing: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text('${sale.currency} ${sale.total}',
                style: const TextStyle(fontWeight: FontWeight.w700)),
            const SizedBox(height: 2),
            Text(sale.status,
                style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                    color: completed
                        ? Colors.green.shade700
                        : PosTheme.textMuted)),
          ],
        ),
      ),
    );
  }

  String _time(DateTime value) {
    final local = value.toLocal();
    final hour = local.hour % 12 == 0 ? 12 : local.hour % 12;
    final minute = local.minute.toString().padLeft(2, '0');
    final period = local.hour >= 12 ? 'PM' : 'AM';
    return '$hour:$minute $period';
  }
}

class _ReturnLine extends StatelessWidget {
  const _ReturnLine(
      {required this.item,
      required this.remaining,
      required this.selected,
      required this.onChanged});
  final PosReceiptItem item;
  final int remaining;
  final int selected;
  final ValueChanged<int>? onChanged;

  @override
  Widget build(BuildContext context) => Card(
          child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(children: [
          Checkbox(
            value: selected > 0,
            onChanged: remaining == 0 || onChanged == null
                ? null
                : (checked) => onChanged!(checked == true ? 1 : 0),
          ),
          Expanded(
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                Text(item.productName,
                    style: const TextStyle(fontWeight: FontWeight.w700)),
                if (item.options.isNotEmpty)
                  Text(item.options.map((o) => o.optionName).join(' · '),
                      style: const TextStyle(
                          fontSize: 12, color: PosTheme.textMuted)),
                Text(
                    'Purchased ${item.quantity} · already returned '
                    '${item.returnedQuantity} · remaining $remaining',
                    style: const TextStyle(
                        fontSize: 12, color: PosTheme.textMuted)),
              ])),
          Text('${item.unitPrice} each'),
          const SizedBox(width: 10),
          IconButton(
              onPressed: selected > 0 && onChanged != null
                  ? () => onChanged!(selected - 1)
                  : null,
              icon: const Icon(Icons.remove_circle_outline)),
          Text('$selected',
              style: const TextStyle(fontWeight: FontWeight.bold)),
          IconButton(
              onPressed: selected < remaining && onChanged != null
                  ? () => onChanged!(selected + 1)
                  : null,
              icon: const Icon(Icons.add_circle_outline)),
        ]),
      ));
}
