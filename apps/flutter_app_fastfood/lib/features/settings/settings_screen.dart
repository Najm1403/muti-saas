// features/settings/settings_screen.dart
//
// Device settings: shop / branch / device info, sync status + last sync +
// Sync now, and Re-validate device.

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../providers/auth_notifier.dart';
import '../../providers/connectivity_provider.dart';
import '../../providers/database_provider.dart';
import '../../providers/menu_provider.dart';
import '../../providers/onboarding_notifier.dart';
import '../../providers/repository_providers.dart';
import '../../services/bluetooth_printer_service.dart';
import '../../services/pdf_service.dart';
import '../pos/pos_theme.dart';
import '../staff/widgets/admin_pin_sheet.dart';

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  bool _syncing = false;
  String? _syncMsg;
  DateTime? _lastSync;
  List<ConnectivityResult> _conn = const [ConnectivityResult.none];
  ReceiptPrintLayout _receiptLayout = ReceiptPrintLayout.a4;
  String _thermalTransport = 'bluetooth';
  String? _printerAddress;
  String? _printerName;
  List<BluetoothPrinterDevice> _bluetoothPrinters = const [];
  bool _scanningPrinters = false;
  final _bluetoothPrinter = BluetoothPrinterService();

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final dao = ref.read(appDatabaseProvider).settingsDao;
    final last = await dao.getLastSyncAt();
    final receiptLayout =
        ReceiptPrintLayout.fromStorage(await dao.getReceiptPrintLayout());
    final thermalTransport = await dao.getThermalPrintTransport();
    final printerAddress = await dao.getBluetoothPrinterAddress();
    final printerName = await dao.getBluetoothPrinterName();
    final conn = await Connectivity().checkConnectivity();
    if (mounted) {
      setState(() {
        _lastSync = last;
        _conn = conn;
        _receiptLayout = receiptLayout;
        _thermalTransport = thermalTransport;
        _printerAddress = printerAddress;
        _printerName = printerName;
      });
    }
  }

  bool get _online => hasApiConnectivity(_conn);

  Future<void> _syncNow() async {
    setState(() {
      _syncing = true;
      _syncMsg = null;
    });
    try {
      await ref.read(syncRepositoryProvider).deltaSync();
      ref.invalidate(categoriesProvider);
      ref.invalidate(allActiveProductsProvider);
      ref.invalidate(productStockProvider);
      ref.invalidate(lowStockThresholdProvider);
      ref.invalidate(lowStockCountProvider);
      await _load();
      if (mounted) setState(() => _syncMsg = 'Sync complete');
    } catch (e) {
      if (mounted) setState(() => _syncMsg = 'Sync failed: $e');
    } finally {
      if (mounted) setState(() => _syncing = false);
    }
  }

  Future<void> _revalidate() async {
    final creds = await showAdminPinSheet(
      context,
      title: 'Deactivate this device',
      subtitle: 'Signs the device out and returns to the activation screen. '
          'A new activation code will be required.',
    );
    if (creds == null || !mounted) return;
    ref.read(authNotifierProvider.notifier).cashierLogout();
    await ref.read(onboardingNotifierProvider.notifier).resetOnboarding();
    if (mounted) context.go('/activate');
  }

  Future<void> _testPrinter() async {
    try {
      if (_receiptLayout == ReceiptPrintLayout.thermal80 &&
          _thermalTransport == 'bluetooth') {
        final address = _printerAddress;
        if (address == null || address.isEmpty) {
          throw const BluetoothPrinterException(
              'Select and save a paired Bluetooth printer first.');
        }
        await _bluetoothPrinter.printTest(address);
      } else {
        await PdfService().printTestPage(layout: _receiptLayout);
      }
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Printer test sent successfully.')),
        );
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Could not open the printer: $error')),
        );
      }
    }
  }

  Future<void> _scanBluetoothPrinters() async {
    setState(() => _scanningPrinters = true);
    try {
      final printers = await _bluetoothPrinter.pairedPrinters();
      if (!mounted) return;
      setState(() => _bluetoothPrinters = printers);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(printers.isEmpty
            ? 'No printer found. Pair the Speed-X printer in device Bluetooth settings, then scan again.'
            : '${printers.length} Bluetooth device(s) found.'),
      ));
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('$error')));
      }
    } finally {
      if (mounted) setState(() => _scanningPrinters = false);
    }
  }

  List<BluetoothPrinterDevice> get _availablePrinters {
    final byAddress = <String, BluetoothPrinterDevice>{
      for (final printer in _bluetoothPrinters) printer.address: printer,
    };
    if (_printerAddress?.isNotEmpty == true) {
      byAddress.putIfAbsent(
        _printerAddress!,
        () => BluetoothPrinterDevice(
          name: _printerName ?? 'Saved thermal printer',
          address: _printerAddress!,
        ),
      );
    }
    return byAddress.values.toList();
  }

  Future<void> _selectBluetoothPrinter(String? address) async {
    if (address == null) return;
    final printer =
        _availablePrinters.firstWhere((item) => item.address == address);
    await ref.read(appDatabaseProvider).settingsDao.saveBluetoothPrinter(
          address: printer.address,
          name: printer.name,
        );
    if (mounted) {
      setState(() {
        _printerAddress = printer.address;
        _printerName = printer.name;
      });
    }
  }

  Future<void> _setThermalTransport(String? value) async {
    if (value == null) return;
    await ref
        .read(appDatabaseProvider)
        .settingsDao
        .setThermalPrintTransport(value);
    if (mounted) setState(() => _thermalTransport = value);
  }

  Future<void> _setReceiptLayout(ReceiptPrintLayout? layout) async {
    if (layout == null) return;
    await ref
        .read(appDatabaseProvider)
        .settingsDao
        .setReceiptPrintLayout(layout.storageValue);
    if (!mounted) return;
    setState(() => _receiptLayout = layout);
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(layout == ReceiptPrintLayout.a4
          ? 'A4 receipt format selected.'
          : '80 mm thermal receipt format selected.'),
    ));
  }

  @override
  Widget build(BuildContext context) {
    final onboarding = ref.watch(onboardingNotifierProvider).valueOrNull;
    final auth = ref.watch(authNotifierProvider).valueOrNull;

    return Scaffold(
      backgroundColor: PosTheme.bg,
      appBar: AppBar(
        backgroundColor: PosTheme.bg,
        elevation: 0,
        foregroundColor: PosTheme.text,
        title: const Text('Settings'),
      ),
      body: Align(
        alignment: Alignment.topCenter,
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 560),
          child: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              _section('Device'),
              _info('Shop', onboarding?.businessName ?? '—'),
              _info('Branch', onboarding?.branchName ?? '—'),
              _info('Device',
                  onboarding?.deviceName ?? auth?.deviceName ?? 'POS'),
              _info('Type', onboarding?.deviceType ?? 'POS'),
              _info('Currency', onboarding?.currency ?? 'Rs.'),
              const SizedBox(height: 20),
              _section('Sync'),
              _info('Status', _online ? 'Online' : 'Offline'),
              _info(
                'Last sync',
                _lastSync == null
                    ? 'Never'
                    : _lastSync!.toLocal().toString().split('.').first,
              ),
              const SizedBox(height: 10),
              FilledButton.icon(
                onPressed: (_syncing || !_online) ? null : _syncNow,
                icon: _syncing
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(
                            strokeWidth: 2, color: Colors.white),
                      )
                    : const Icon(Icons.sync, size: 18),
                style: FilledButton.styleFrom(
                  backgroundColor: PosTheme.accent,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: const RoundedRectangleBorder(
                      borderRadius: PosTheme.pillRadius),
                ),
                label: const Text('Sync now'),
              ),
              if (_syncMsg != null) ...[
                const SizedBox(height: 8),
                Text(_syncMsg!,
                    style: const TextStyle(
                        fontSize: 12, color: PosTheme.textMuted)),
              ],
              const SizedBox(height: 28),
              _section('Printer'),
              DropdownButtonFormField<ReceiptPrintLayout>(
                key: ValueKey(_receiptLayout),
                initialValue: _receiptLayout,
                decoration: const InputDecoration(
                  labelText: 'Receipt print and PDF format',
                  border: OutlineInputBorder(),
                  helperText: 'Used for Print and PDF/Share on this device.',
                ),
                items: const [
                  DropdownMenuItem(
                    value: ReceiptPrintLayout.a4,
                    child: Text('A4 - desktop / laser printer'),
                  ),
                  DropdownMenuItem(
                    value: ReceiptPrintLayout.thermal80,
                    child: Text('80 mm - thermal receipt printer'),
                  ),
                ],
                onChanged: _setReceiptLayout,
              ),
              const SizedBox(height: 12),
              if (_receiptLayout == ReceiptPrintLayout.thermal80) ...[
                DropdownButtonFormField<String>(
                  key: ValueKey(_thermalTransport),
                  initialValue: _thermalTransport,
                  decoration: const InputDecoration(
                    labelText: '80 mm printer connection',
                    border: OutlineInputBorder(),
                  ),
                  items: const [
                    DropdownMenuItem(
                      value: 'bluetooth',
                      child: Text('Direct Bluetooth ESC/POS (fast)'),
                    ),
                    DropdownMenuItem(
                      value: 'system',
                      child: Text('System printer driver / dialog'),
                    ),
                  ],
                  onChanged: _setThermalTransport,
                ),
                const SizedBox(height: 12),
                if (_thermalTransport == 'bluetooth') ...[
                  const Text(
                    'Pair the Speed-X printer in Windows or Android Bluetooth settings first. '
                    'Then scan and select it here. Direct mode prints without a preview dialog.',
                    style: TextStyle(fontSize: 12, color: PosTheme.textMuted),
                  ),
                  const SizedBox(height: 10),
                  OutlinedButton.icon(
                    onPressed:
                        _scanningPrinters ? null : _scanBluetoothPrinters,
                    icon: _scanningPrinters
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.bluetooth_searching, size: 18),
                    label: Text(_scanningPrinters
                        ? 'Scanning Bluetooth devices...'
                        : 'Scan paired Bluetooth printers'),
                  ),
                  if (_availablePrinters.isNotEmpty) ...[
                    const SizedBox(height: 10),
                    DropdownButtonFormField<String>(
                      key: ValueKey(
                          '${_printerAddress ?? ''}-${_availablePrinters.length}'),
                      initialValue: _printerAddress,
                      isExpanded: true,
                      decoration: const InputDecoration(
                        labelText: 'Selected Bluetooth printer',
                        border: OutlineInputBorder(),
                      ),
                      items: _availablePrinters
                          .map((printer) => DropdownMenuItem(
                                value: printer.address,
                                child: Text(
                                  '${printer.name} (${printer.address})',
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ))
                          .toList(),
                      onChanged: _selectBluetoothPrinter,
                    ),
                  ],
                  const SizedBox(height: 12),
                ],
              ],
              const Text(
                'A4 and system-driver mode use the operating-system print dialog. '
                'Direct Bluetooth mode sends an 80 mm ESC/POS receipt immediately.',
                style: TextStyle(fontSize: 12, color: PosTheme.textMuted),
              ),
              const SizedBox(height: 10),
              OutlinedButton.icon(
                onPressed: _testPrinter,
                icon: const Icon(Icons.print_outlined, size: 18),
                label: Text(_receiptLayout == ReceiptPrintLayout.thermal80 &&
                        _thermalTransport == 'bluetooth'
                    ? 'Connect and print Bluetooth test receipt'
                    : 'Open printer / Print test page'),
              ),
              const SizedBox(height: 28),
              _section('Danger zone'),
              OutlinedButton.icon(
                onPressed: _revalidate,
                icon: const Icon(Icons.link_off, size: 18),
                style: OutlinedButton.styleFrom(
                  foregroundColor: const Color(0xFFD84315),
                  side: const BorderSide(color: Color(0xFFF3C6BA), width: 2),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: const RoundedRectangleBorder(
                      borderRadius: PosTheme.pillRadius),
                ),
                label: const Text('Deactivate this device'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _section(String t) => Padding(
        padding: const EdgeInsets.only(bottom: 8),
        child: Text(t.toUpperCase(),
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              letterSpacing: 1.4,
              color: PosTheme.accentText,
            )),
      );

  Widget _info(String label, String value) => Container(
        margin: const EdgeInsets.only(bottom: 4),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
        decoration: BoxDecoration(
          color: PosTheme.surface,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: PosTheme.divider),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SizedBox(
              width: 120,
              child: Text(label,
                  style:
                      const TextStyle(fontSize: 14, color: PosTheme.textMuted)),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(value,
                  textAlign: TextAlign.left,
                  style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                      color: PosTheme.text)),
            ),
          ],
        ),
      );
}
