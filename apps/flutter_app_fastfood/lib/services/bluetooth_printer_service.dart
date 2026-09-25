import 'dart:async';
import 'dart:convert';

import 'package:esc_pos_utils_plus/esc_pos_utils_plus.dart';
import 'package:image/image.dart' as img;
import 'package:intl/intl.dart';
import 'package:print_bluetooth_thermal/print_bluetooth_thermal.dart';

import '../core/models/sale/pos_receipt_item.dart';
import '../core/models/sale/pos_receipt_response.dart';

class BluetoothPrinterDevice {
  const BluetoothPrinterDevice({required this.name, required this.address});

  final String name;
  final String address;
}

class BluetoothPrinterException implements Exception {
  const BluetoothPrinterException(this.message);
  final String message;

  @override
  String toString() => message;
}

/// Direct 80 mm ESC/POS printing for paired Bluetooth thermal printers.
///
/// Pairing stays in the operating system where the PIN dialog belongs. The POS
/// discovers paired/visible devices, remembers one address, reconnects when
/// needed, and sends raw ESC/POS bytes without opening a print preview.
class BluetoothPrinterService {
  static String? _connectedAddress;
  static final _money = NumberFormat('#,##0.00');
  static final _date = DateFormat('dd MMM yyyy HH:mm');

  Future<List<BluetoothPrinterDevice>> pairedPrinters() async {
    final permitted = await PrintBluetoothThermal.isPermissionBluetoothGranted
        .timeout(const Duration(seconds: 15));
    if (!permitted) {
      throw const BluetoothPrinterException(
          'Bluetooth permission was not granted. Allow Nearby devices for Storixx.');
    }
    final enabled = await PrintBluetoothThermal.bluetoothEnabled
        .timeout(const Duration(seconds: 15));
    if (!enabled) {
      throw const BluetoothPrinterException(
          'Bluetooth is turned off. Turn it on and pair the printer first.');
    }
    final devices = await PrintBluetoothThermal.pairedBluetooths
        .timeout(const Duration(seconds: 20));
    final unique = <String, BluetoothPrinterDevice>{};
    for (final device in devices) {
      if (device.macAdress.trim().isEmpty) continue;
      unique[device.macAdress] = BluetoothPrinterDevice(
        name: device.name.trim().isEmpty ? 'Thermal printer' : device.name,
        address: device.macAdress,
      );
    }
    final result = unique.values.toList()
      ..sort((a, b) => a.name.toLowerCase().compareTo(b.name.toLowerCase()));
    return result;
  }

  Future<void> connect(String address) async {
    if (_connectedAddress == address &&
        await PrintBluetoothThermal.connectionStatus) {
      return;
    }
    if (await PrintBluetoothThermal.connectionStatus) {
      await PrintBluetoothThermal.disconnect;
    }
    final connected =
        await PrintBluetoothThermal.connect(macPrinterAddress: address)
            .timeout(const Duration(seconds: 20));
    if (!connected) {
      _connectedAddress = null;
      throw const BluetoothPrinterException(
          'Could not connect. Confirm the printer is on, paired, and not connected to another device.');
    }
    _connectedAddress = address;
  }

  Future<void> disconnect() async {
    await PrintBluetoothThermal.disconnect.timeout(const Duration(seconds: 10));
    _connectedAddress = null;
  }

  Future<void> printTest(String address) async {
    await connect(address);
    final profile = await CapabilityProfile.load();
    final generator = Generator(PaperSize.mm80, profile);
    final bytes = <int>[
      ...generator.reset(),
      ...generator.text('STORIXX',
          styles: const PosStyles(
              align: PosAlign.center,
              bold: true,
              height: PosTextSize.size2,
              width: PosTextSize.size2)),
      ...generator.text('Bluetooth printer connected',
          styles: const PosStyles(align: PosAlign.center)),
      ...generator.text(_date.format(DateTime.now()),
          styles: const PosStyles(align: PosAlign.center)),
      ...generator.hr(),
      ...generator.text('80 mm ESC/POS test successful',
          styles: const PosStyles(align: PosAlign.center, bold: true)),
      ...generator.feed(3),
      ...generator.cut(mode: PosCutMode.partial),
    ];
    await _write(bytes);
  }

  Future<void> printReceipt(String address, PosReceiptResponse receipt) async {
    await connect(address);
    final bytes = await buildReceiptBytes(receipt);
    await _write(bytes);
  }

  Future<void> _write(List<int> bytes) async {
    final printed = await PrintBluetoothThermal.writeBytes(bytes)
        .timeout(const Duration(seconds: 30));
    if (!printed) {
      throw const BluetoothPrinterException(
          'The printer connection was lost before the receipt was sent.');
    }
  }

  Future<List<int>> buildReceiptBytes(PosReceiptResponse receipt) async {
    final profile = await CapabilityProfile.load();
    final generator = Generator(PaperSize.mm80, profile);
    final bytes = <int>[...generator.reset()];

    if (receipt.receiptLogoBase64?.isNotEmpty ?? false) {
      try {
        final decoded =
            img.decodeImage(base64Decode(receipt.receiptLogoBase64!));
        if (decoded != null) {
          final logo = img.copyResize(decoded, width: 300);
          bytes.addAll(generator.imageRaster(logo,
              align: PosAlign.center, imageFn: PosImageFn.bitImageRaster));
        }
      } catch (_) {
        // Branding text still prints when cached image bytes are damaged.
      }
    }

    final shop = receipt.businessName.isEmpty
        ? receipt.branchName
        : receipt.businessName;
    bytes.addAll(generator.text(_safe(shop),
        styles: const PosStyles(
            align: PosAlign.center,
            bold: true,
            height: PosTextSize.size2,
            width: PosTextSize.size2)));
    if (receipt.receiptTagline?.isNotEmpty ?? false) {
      bytes.addAll(generator.text(_safe(receipt.receiptTagline!),
          styles: const PosStyles(align: PosAlign.center)));
    }
    bytes.addAll(generator.text(
        _safe(
            '${receipt.branchName}${receipt.branchCode.isEmpty ? '' : ' (${receipt.branchCode})'}'),
        styles: const PosStyles(align: PosAlign.center, bold: true)));
    if (receipt.branchAddress?.isNotEmpty ?? false) {
      bytes.addAll(generator.text(_safe(receipt.branchAddress!),
          styles: const PosStyles(align: PosAlign.center)));
    }
    if (receipt.branchPhone?.isNotEmpty ?? false) {
      bytes.addAll(generator.text(_safe('Ph: ${receipt.branchPhone}'),
          styles: const PosStyles(align: PosAlign.center)));
    }

    bytes.addAll(generator.hr());
    if (receipt.status != 'COMPLETED') {
      bytes.addAll(generator.text(_safe(receipt.status),
          styles: const PosStyles(align: PosAlign.center, bold: true)));
    }
    bytes.addAll(generator.text(_safe('Receipt: ${receipt.saleNumber}')));
    bytes.addAll(generator
        .text(_safe('Date: ${_date.format(receipt.soldAt.toLocal())}')));
    bytes.addAll(generator.text(_safe('Cashier: ${receipt.cashierName}')));
    bytes.addAll(generator.hr());
    bytes.addAll(generator.row([
      PosColumn(text: 'ITEM', width: 5, styles: const PosStyles(bold: true)),
      PosColumn(
          text: 'QTY',
          width: 1,
          styles: const PosStyles(bold: true, align: PosAlign.right)),
      PosColumn(
          text: 'UNIT',
          width: 3,
          styles: const PosStyles(bold: true, align: PosAlign.right)),
      PosColumn(
          text: 'AMOUNT',
          width: 3,
          styles: const PosStyles(bold: true, align: PosAlign.right)),
    ]));

    // Components must sit directly under their base line, same ordering as
    // the on-screen preview and both PDF layouts — not the server's raw order.
    for (final item in groupReceiptItemsForDisplay(receipt.items)) {
      final prefix = item.parentItemId == null ? '' : '- ';
      bytes.addAll(generator.row([
        PosColumn(text: _safe('$prefix${item.productName}'), width: 5),
        PosColumn(
            text: _safe(item.quantity),
            width: 1,
            styles: const PosStyles(align: PosAlign.right)),
        PosColumn(
            text: _amount(item.unitPrice, receipt.currency),
            width: 3,
            styles: const PosStyles(align: PosAlign.right)),
        PosColumn(
            text: _amount(item.total, receipt.currency),
            width: 3,
            styles: const PosStyles(align: PosAlign.right)),
      ]));
      for (final option in item.options) {
        bytes.addAll(generator.text(_safe('  + ${option.optionName}')));
      }
      for (final addon in item.addons) {
        bytes.addAll(generator.text(_safe(addon.wasRemoved
            ? '  - No ${addon.name}'
            : '  + ${addon.name}  ${_amount(addon.priceDelta, receipt.currency)}')));
      }
    }

    bytes.addAll(generator.hr());
    _total(bytes, generator, 'Subtotal', receipt.subtotal, receipt.currency);
    if ((double.tryParse(receipt.discount) ?? 0) > 0) {
      _total(bytes, generator, 'Discount', receipt.discount, receipt.currency,
          negative: true);
    }
    if ((double.tryParse(receipt.taxAmount) ?? 0) > 0) {
      _total(bytes, generator, 'Tax', receipt.taxAmount, receipt.currency);
    }
    _total(bytes, generator, 'TOTAL', receipt.total, receipt.currency,
        strong: true);
    bytes.addAll(generator.hr());
    for (final payment in receipt.payments) {
      _total(bytes, generator, payment.paymentMethod, payment.amount,
          receipt.currency);
    }
    if ((double.tryParse(receipt.change) ?? 0) > 0) {
      _total(bytes, generator, 'Change', receipt.change, receipt.currency);
    }
    bytes.addAll(generator.feed(1));
    bytes.addAll(generator.text(
        _safe(receipt.receiptThankYou?.isNotEmpty == true
            ? receipt.receiptThankYou!
            : 'THANK YOU!'),
        styles: const PosStyles(align: PosAlign.center, bold: true)));
    if (receipt.receiptTerms?.isNotEmpty ?? false) {
      bytes.addAll(generator.hr());
      bytes.addAll(generator.text(_safe(receipt.receiptTerms!),
          styles: const PosStyles(align: PosAlign.center)));
    }
    bytes.addAll(generator.text(
        _safe('Storixx · developed by apkaysoftware.com'),
        styles: const PosStyles(align: PosAlign.center)));
    bytes.addAll(generator.text(_safe('03487457766'),
        styles: const PosStyles(align: PosAlign.center)));
    bytes.addAll(generator.feed(3));
    bytes.addAll(generator.cut(mode: PosCutMode.partial));
    return bytes;
  }

  static void _total(List<int> bytes, Generator generator, String label,
      String amount, String currency,
      {bool negative = false, bool strong = false}) {
    bytes.addAll(generator.row([
      PosColumn(text: _safe(label), width: 7, styles: PosStyles(bold: strong)),
      PosColumn(
          text: '${negative ? '-' : ''}${_amount(amount, currency)}',
          width: 5,
          styles: PosStyles(align: PosAlign.right, bold: strong)),
    ]));
  }

  static String _amount(String value, String currency) =>
      '$currency ${_money.format(double.tryParse(value) ?? 0)}';

  /// Most low-cost ESC/POS printers use a single-byte code page. Replacing
  /// unsupported glyphs avoids a codec exception that would abort a sale print.
  static String _safe(String value) =>
      String.fromCharCodes(value.runes.map((rune) => rune <= 255 ? rune : 63));
}
