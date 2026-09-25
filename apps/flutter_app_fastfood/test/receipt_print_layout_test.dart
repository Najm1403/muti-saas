import 'package:drift/native.dart';
import 'package:fastfood_pos/db/app_database.dart';
import 'package:fastfood_pos/core/models/sale/pos_receipt_item.dart';
import 'package:fastfood_pos/core/models/sale/pos_receipt_payment.dart';
import 'package:fastfood_pos/core/models/sale/pos_receipt_response.dart';
import 'package:fastfood_pos/services/bluetooth_printer_service.dart';
import 'package:fastfood_pos/services/pdf_service.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('receipt print layout defaults to A4 and persists thermal selection',
      () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());

    expect(await db.settingsDao.getReceiptPrintLayout(), 'a4');
    expect(ReceiptPrintLayout.fromStorage('unexpected'), ReceiptPrintLayout.a4);

    await db.settingsDao.setReceiptPrintLayout('thermal80');
    expect(await db.settingsDao.getReceiptPrintLayout(), 'thermal80');
    expect(ReceiptPrintLayout.fromStorage('thermal80'),
        ReceiptPrintLayout.thermal80);

    expect(
      () => db.settingsDao.setReceiptPrintLayout('letter'),
      throwsArgumentError,
    );
    await db.settingsDao
        .saveBluetoothPrinter(address: 'AA:BB:CC:DD:EE:FF', name: 'Speed-X');
    expect(
        await db.settingsDao.getBluetoothPrinterAddress(), 'AA:BB:CC:DD:EE:FF');
    expect(await db.settingsDao.getBluetoothPrinterName(), 'Speed-X');
    await db.settingsDao.setThermalPrintTransport('system');
    expect(await db.settingsDao.getThermalPrintTransport(), 'system');
    await db.close();
  });

  test('80 mm ESC/POS receipt bytes include content and cut command', () async {
    final receipt = PosReceiptResponse(
      saleId: 'sale-1',
      saleNumber: 'LHR01-26-000128',
      soldAt: DateTime.utc(2026, 9, 19, 16, 20),
      branchName: 'Lahore Main',
      branchCode: 'LHR01',
      branchPhone: '042-111-123-456',
      businessName: 'Storixx',
      currency: 'Rs.',
      receiptTagline: 'Shop smart live better',
      receiptThankYou: 'Thank you!',
      receiptTerms: 'Returns within 7 days — receipt required.',
      cashierName: 'Cashier',
      items: const [
        PosReceiptItem(
          productName: '4GB RAM',
          quantity: '1',
          unitPrice: '2000.00',
          discount: '0.00',
          total: '2000.00',
        ),
      ],
      subtotal: '2000.00',
      discount: '0.00',
      taxAmount: '0.00',
      total: '2000.00',
      payments: const [
        PosReceiptPayment(paymentMethod: 'Cash', amount: '2000.00'),
      ],
      change: '0.00',
    );

    final bytes = await BluetoothPrinterService().buildReceiptBytes(receipt);
    expect(bytes.length, greaterThan(150));
    expect(bytes, containsAllInOrder('LHR01-26-000128'.codeUnits));
    expect(bytes, containsAllInOrder('4GB RAM'.codeUnits));
    expect(bytes, contains(0x1d));
  });
}
