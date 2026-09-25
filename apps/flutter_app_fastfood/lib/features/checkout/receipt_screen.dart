// features/checkout/receipt_screen.dart
//
// Shown after a completed online sale (/pos/receipt/:id).
//
// The receipt object is handed over via [lastReceiptProvider]; if it is missing
// (e.g. a deep link or app relaunch) it is re-fetched from the server by id.
// Buttons: Print, Share (both via PdfService) and New Order.

import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../core/models/sale/pos_receipt_item.dart';
import '../../core/models/sale/pos_receipt_response.dart';
import '../../providers/currency_provider.dart';
import '../../providers/database_provider.dart';
import '../../providers/repository_providers.dart';
import '../../services/bluetooth_printer_service.dart';
import '../../services/pdf_service.dart';
import '../common/pill_button.dart';
import '../pos/pos_theme.dart';
import 'last_receipt_provider.dart';

class ReceiptScreen extends ConsumerStatefulWidget {
  final String saleId;
  const ReceiptScreen({super.key, required this.saleId});

  @override
  ConsumerState<ReceiptScreen> createState() => _ReceiptScreenState();
}

class _ReceiptScreenState extends ConsumerState<ReceiptScreen> {
  final _pdf = PdfService();
  late Future<PosReceiptResponse> _receiptFuture;

  @override
  void initState() {
    super.initState();
    final cached = ref.read(lastReceiptProvider);
    _receiptFuture = (cached != null && cached.saleId == widget.saleId)
        ? Future.value(cached)
        : ref.read(saleRepositoryProvider).getReceipt(widget.saleId);
  }

  void _newOrder() {
    ref.read(lastReceiptProvider.notifier).state = null;
    context.go('/pos');
  }

  Future<ReceiptPrintLayout> _selectedPrintLayout() async {
    final value =
        await ref.read(appDatabaseProvider).settingsDao.getReceiptPrintLayout();
    return ReceiptPrintLayout.fromStorage(value);
  }

  Future<void> _print(PosReceiptResponse receipt) async {
    try {
      final dao = ref.read(appDatabaseProvider).settingsDao;
      final layout = await _selectedPrintLayout();
      final transport = await dao.getThermalPrintTransport();
      if (layout == ReceiptPrintLayout.thermal80 && transport == 'bluetooth') {
        final address = await dao.getBluetoothPrinterAddress();
        if (address == null || address.isEmpty) {
          throw const BluetoothPrinterException(
              'No Bluetooth printer selected. Open Settings > Printer first.');
        }
        await BluetoothPrinterService().printReceipt(address, receipt);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Thermal receipt printed.')));
        }
        return;
      }
      await _pdf.printReceipt(receipt, layout: layout);
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Could not print receipt: $error')),
        );
      }
    }
  }

  Future<void> _sharePdf(PosReceiptResponse receipt) async {
    await _pdf.shareReceipt(receipt, layout: await _selectedPrintLayout());
  }

  Future<void> _cancelBill(PosReceiptResponse receipt) async {
    final controller = TextEditingController();
    final reason = await showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Cancel Order / Bill'),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          Text('Cancel ${receipt.saleNumber} in full?'),
          const SizedBox(height: 12),
          TextField(
            controller: controller,
            autofocus: true,
            maxLength: 500,
            decoration: const InputDecoration(
              labelText: 'Reason (required)',
              hintText: 'For example: order entered twice',
              border: OutlineInputBorder(),
            ),
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
    try {
      final result = await ref
          .read(saleRepositoryProvider)
          .cancelSale(receipt.saleId, reason);
      if (!mounted) return;
      setState(() {
        _receiptFuture =
            ref.read(saleRepositoryProvider).getReceipt(receipt.saleId);
      });
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content:
            Text('Bill cancelled. ${result['refund_number']} was recorded.'),
        backgroundColor: Colors.green.shade700,
      ));
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('Could not cancel bill: $error'),
          backgroundColor: Colors.red.shade700,
        ));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: PosTheme.surface,
      appBar: AppBar(
        backgroundColor: PosTheme.bg,
        elevation: 0,
        foregroundColor: PosTheme.text,
        automaticallyImplyLeading: false,
        title: const Text('Receipt',
            style: TextStyle(fontWeight: FontWeight.w700)),
        actions: [
          TextButton(
            onPressed: () => context.go('/dashboard'),
            child: const Text('Dashboard'),
          ),
          TextButton(onPressed: _newOrder, child: const Text('New Order')),
          const SizedBox(width: 8),
        ],
      ),
      body: FutureBuilder<PosReceiptResponse>(
        future: _receiptFuture,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snap.hasError || !snap.hasData) {
            return _Problem(onNewOrder: _newOrder);
          }
          return _ReceiptBody(
            receipt: snap.data!,
            onPrint: () => _print(snap.data!),
            onShare: () => _sharePdf(snap.data!),
            onCancel: snap.data!.status == 'COMPLETED'
                ? () => _cancelBill(snap.data!)
                : null,
            onNewOrder: _newOrder,
          );
        },
      ),
    );
  }
}

class _ReceiptBody extends ConsumerWidget {
  final PosReceiptResponse receipt;
  final VoidCallback onPrint;
  final VoidCallback onShare;
  final VoidCallback? onCancel;
  final VoidCallback onNewOrder;

  const _ReceiptBody({
    required this.receipt,
    required this.onPrint,
    required this.onShare,
    this.onCancel,
    required this.onNewOrder,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final money = ref.watch(moneyProvider);
    final df = DateFormat('dd MMM yyyy · HH:mm');
    final logoBytes = _decodeLogo(receipt.receiptLogoBase64);

    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 460),
        child: ListView(
          padding: const EdgeInsets.all(24),
          children: [
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(20),
                boxShadow: PosTheme.shadowMd,
              ),
              child: Column(
                children: [
                  if (logoBytes != null)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Image.memory(logoBytes,
                          height: 60,
                          fit: BoxFit.contain,
                          errorBuilder: (_, __, ___) =>
                              const SizedBox.shrink()),
                    ),
                  Text(
                    receipt.businessName.isEmpty
                        ? receipt.branchName
                        : receipt.businessName,
                    style: const TextStyle(
                        fontSize: 23, fontWeight: FontWeight.w900),
                  ),
                  if (receipt.receiptTagline?.isNotEmpty ?? false)
                    Text(receipt.receiptTagline!,
                        style: const TextStyle(
                            color: PosTheme.textMuted,
                            fontSize: 12,
                            letterSpacing: 1.1)),
                  const Divider(height: 24),
                  Align(
                    alignment: Alignment.centerLeft,
                    child: Text(
                      '${receipt.branchName}${receipt.branchCode.isEmpty ? '' : ' (${receipt.branchCode})'}',
                      style: const TextStyle(fontWeight: FontWeight.w700),
                    ),
                  ),
                  if (receipt.branchAddress?.isNotEmpty ?? false)
                    Align(
                        alignment: Alignment.centerLeft,
                        child: Text(receipt.branchAddress!,
                            style: const TextStyle(
                                color: PosTheme.textMuted, fontSize: 12))),
                  if (receipt.branchPhone?.isNotEmpty ?? false)
                    Align(
                        alignment: Alignment.centerLeft,
                        child: Text('Ph: ${receipt.branchPhone}',
                            style: const TextStyle(
                                color: PosTheme.textMuted, fontSize: 12))),
                  const SizedBox(height: 10),
                  if (receipt.status != 'COMPLETED')
                    Padding(
                      padding: const EdgeInsets.only(bottom: 6),
                      child: Center(
                        child: Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: Colors.red.shade50,
                            borderRadius: BorderRadius.circular(6),
                            border: Border.all(color: Colors.red.shade200),
                          ),
                          child: Text(receipt.status,
                              style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.w800,
                                  letterSpacing: 1,
                                  color: Colors.red.shade700)),
                        ),
                      ),
                    ),
                  _kv('Receipt #', receipt.saleNumber),
                  _kv('Date', df.format(receipt.soldAt.toLocal())),
                  _kv('Cashier', receipt.cashierName),
                  const Divider(height: 24),
                  ...groupReceiptItemsForDisplay(receipt.items).map((it) {
                    final isComponent = it.parentItemId != null;
                    return Padding(
                      padding: EdgeInsets.only(
                          left: isComponent ? 16 : 0, top: 4, bottom: 4),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Expanded(
                                child: Text(
                                  isComponent
                                      ? '↳ ${it.quantity} × ${it.productName}'
                                      : '${it.quantity} × ${it.productName}',
                                  style: TextStyle(
                                      fontWeight: FontWeight.w600,
                                      fontSize: isComponent ? 13 : null,
                                      color: isComponent
                                          ? PosTheme.textMuted
                                          : null),
                                ),
                              ),
                              Text(money(it.total)),
                            ],
                          ),
                          if (!isComponent)
                            Padding(
                              padding: const EdgeInsets.only(left: 12, top: 2),
                              child: Text('${money(it.unitPrice)} each',
                                  style: const TextStyle(
                                      fontSize: 11, color: PosTheme.textMuted)),
                            ),
                          for (final o in it.options)
                            Padding(
                              padding: const EdgeInsets.only(left: 12, top: 2),
                              child: Text('+ ${o.optionName}',
                                  style: const TextStyle(
                                      fontSize: 12, color: PosTheme.textMuted)),
                            ),
                          for (final a in it.addons)
                            Padding(
                              padding: const EdgeInsets.only(left: 12, top: 2),
                              child: Text(
                                  a.wasRemoved
                                      ? '– No ${a.name}'
                                      : _asNum(a.priceDelta) > 0
                                          ? '+ ${a.name} (${money(a.priceDelta)})'
                                          : '+ ${a.name}',
                                  style: const TextStyle(
                                      fontSize: 12, color: PosTheme.textMuted)),
                            ),
                        ],
                      ),
                    );
                  }),
                  const Divider(height: 24),
                  _kv('Subtotal', money(receipt.subtotal)),
                  if (_asNum(receipt.discount) > 0)
                    _kv('Discount', '-${money(receipt.discount)}'),
                  if (_asNum(receipt.taxAmount) > 0)
                    _kv('Tax', money(receipt.taxAmount)),
                  _kv('Total', money(receipt.total), bold: true),
                  const SizedBox(height: 6),
                  ...receipt.payments
                      .map((p) => _kv(p.paymentMethod, money(p.amount))),
                  if (_asNum(receipt.change) > 0)
                    _kv('Change', money(receipt.change)),
                  const SizedBox(height: 22),
                  Text(
                    receipt.receiptThankYou?.isNotEmpty == true
                        ? receipt.receiptThankYou!
                        : 'THANK YOU!',
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.w900,
                        letterSpacing: 2),
                  ),
                  if (receipt.receiptTerms?.isNotEmpty ?? false) ...[
                    const Divider(height: 28),
                    Text(receipt.receiptTerms!,
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                            color: PosTheme.textMuted, fontSize: 11)),
                  ],
                  const SizedBox(height: 10),
                  const Text(
                    'Storixx · developed by apkaysoftware.com · 03487457766',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: PosTheme.textMuted, fontSize: 9),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
            Row(
              children: [
                Expanded(
                  child: PillButton(
                    label: 'Print',
                    icon: Icons.print_outlined,
                    onTap: onPrint,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: PillButton(
                    label: 'Share',
                    icon: Icons.ios_share,
                    secondary: true,
                    onTap: onShare,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            if (onCancel != null) ...[
              PillButton(
                label: 'Cancel Order / Bill',
                icon: Icons.cancel_outlined,
                secondary: true,
                onTap: onCancel!,
              ),
              const SizedBox(height: 12),
            ],
            PillButton(
              label: 'New Order',
              secondary: true,
              onTap: onNewOrder,
            ),
          ],
        ),
      ),
    );
  }

  static num _asNum(String s) => num.tryParse(s) ?? 0;

  /// A damaged cached logo must never prevent the receipt from rendering —
  /// mirrors the guard already used in receipt_pdf_builder.dart.
  static Uint8List? _decodeLogo(String? base64) {
    if (base64 == null || base64.isEmpty) return null;
    try {
      return base64Decode(base64);
    } catch (_) {
      return null;
    }
  }

  Widget _kv(String k, String v, {bool bold = false}) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 3),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(k,
                style:
                    const TextStyle(color: PosTheme.textMuted, fontSize: 14)),
            Text(v,
                style: TextStyle(
                  fontSize: bold ? 17 : 14,
                  fontWeight: bold ? FontWeight.w800 : FontWeight.w600,
                )),
          ],
        ),
      );
}

class _Problem extends StatelessWidget {
  final VoidCallback onNewOrder;
  const _Problem({required this.onNewOrder});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 360),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.receipt_long_outlined,
                size: 44, color: PosTheme.textMuted),
            const SizedBox(height: 12),
            const Text(
              'The sale went through, but the receipt could not be loaded '
              '(you may be offline). It is safe to start the next order.',
              textAlign: TextAlign.center,
              style: TextStyle(color: PosTheme.textMuted),
            ),
            const SizedBox(height: 20),
            PillButton(label: 'New Order', onTap: onNewOrder),
          ],
        ),
      ),
    );
  }
}
