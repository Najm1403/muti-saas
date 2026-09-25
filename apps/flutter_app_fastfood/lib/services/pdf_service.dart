import 'dart:convert';

import 'package:intl/intl.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';

import '../core/models/sale/pos_receipt_item.dart';
import '../core/models/sale/pos_receipt_response.dart';
import '../core/models/session/session_summary_response.dart';
import 'receipt_pdf_builder.dart';

enum ReceiptPrintLayout {
  a4('a4'),
  thermal80('thermal80');

  const ReceiptPrintLayout(this.storageValue);
  final String storageValue;

  static ReceiptPrintLayout fromStorage(String value) =>
      value == thermal80.storageValue ? thermal80 : a4;
}

/// Generates, prints, and shares branded PDF receipts.
///
/// Each method accepts a [PosReceiptResponse] returned by the server after
/// a successful sale, so no local DB lookups are required.
class PdfService {
  static final _dateFormat = DateFormat('dd MMM yyyy HH:mm');
  static final _moneyFormat = NumberFormat('#,##0.00');

  /// Builds an in-memory PDF document from [receipt].
  ///
  /// The layout mimics an 80 mm thermal roll: narrow single-column,
  /// monospaced font — suitable for printing via the Windows/Android system
  /// print dialog to a thermal printer, or for sharing a thermal-formatted PDF.
  Future<pw.Document> generateReceipt(
    PosReceiptResponse receipt, {
    ReceiptPrintLayout layout = ReceiptPrintLayout.a4,
  }) =>
      layout == ReceiptPrintLayout.thermal80
          ? _generateThermal80Receipt(receipt)
          : ReceiptPdfBuilder.build(receipt);

  Future<pw.Document> _generateThermal80Receipt(
      PosReceiptResponse receipt) async {
    final doc = pw.Document();
    final font = pw.Font.courier();
    final boldFont = pw.Font.courierBold();
    // Every monetary field on the receipt is a Decimal-as-string that may be
    // malformed/empty; tryParse (not parse) keeps a bad value from throwing
    // inside the pw.Page build closure and crashing this whole layout, same
    // as every other receipt renderer already guards this.
    String money(String value) =>
        '${receipt.currency} ${_moneyFormat.format(double.tryParse(value) ?? 0)}';
    pw.MemoryImage? logo;
    if (receipt.receiptLogoBase64?.isNotEmpty ?? false) {
      try {
        logo = pw.MemoryImage(base64Decode(receipt.receiptLogoBase64!));
      } catch (_) {
        // Continue without a damaged cached image.
      }
    }
    final thermalHeightMm = 125 +
        (receipt.items.length * 14) +
        (receipt.payments.length * 6) +
        ((receipt.receiptTerms?.isNotEmpty ?? false) ? 18 : 0) +
        8; // fixed developer-credit footer line, always shown

    doc.addPage(pw.Page(
      pageFormat: PdfPageFormat(
          80 * PdfPageFormat.mm, thermalHeightMm * PdfPageFormat.mm,
          marginAll: 4 * PdfPageFormat.mm),
      build: (ctx) => pw.Column(
        crossAxisAlignment: pw.CrossAxisAlignment.start,
        children: [
          // Header
          if (logo != null)
            pw.Center(
                child: pw.SizedBox(
                    width: 36 * PdfPageFormat.mm,
                    height: 18 * PdfPageFormat.mm,
                    child: pw.Image(logo, fit: pw.BoxFit.contain))),
          pw.Center(
            child: pw.Text(
                receipt.businessName.isEmpty
                    ? receipt.branchName
                    : receipt.businessName,
                style: pw.TextStyle(font: boldFont, fontSize: 13)),
          ),
          if (receipt.receiptTagline?.isNotEmpty ?? false)
            pw.Center(
                child: pw.Text(receipt.receiptTagline!,
                    style: pw.TextStyle(font: font, fontSize: 8))),
          pw.Center(
              child: pw.Text(
                  '${receipt.branchName}${receipt.branchCode.isEmpty ? '' : ' (${receipt.branchCode})'}',
                  style: pw.TextStyle(font: font, fontSize: 8))),
          if (receipt.branchPhone?.isNotEmpty ?? false)
            pw.Center(
                child: pw.Text('Ph: ${receipt.branchPhone}',
                    style: pw.TextStyle(font: font, fontSize: 8))),
          pw.SizedBox(height: 4),
          pw.Divider(thickness: 0.5),

          if (receipt.status != 'COMPLETED')
            pw.Center(
                child: pw.Text(receipt.status,
                    style: pw.TextStyle(font: boldFont, fontSize: 10))),
          if (receipt.status != 'COMPLETED') pw.SizedBox(height: 3),

          // Sale metadata
          _row('Receipt #', receipt.saleNumber, font: font, boldFont: boldFont),
          _row('Date', _dateFormat.format(receipt.soldAt.toLocal()),
              font: font, boldFont: boldFont),
          _row('Cashier', receipt.cashierName, font: font, boldFont: boldFont),
          pw.Divider(thickness: 0.5),

          // Line items — components indented directly under their base line.
          ...groupReceiptItemsForDisplay(receipt.items).map((item) {
            final isComponent = item.parentItemId != null;
            final lineTotal = money(item.total);
            final indent = isComponent ? '  ' : '';
            return pw.Padding(
              padding: pw.EdgeInsets.only(left: isComponent ? 6 : 0),
              child: pw.Column(
                crossAxisAlignment: pw.CrossAxisAlignment.start,
                children: [
                  pw.Row(
                    mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
                    children: [
                      pw.Expanded(
                          child: pw.Text(
                              isComponent
                                  ? '$indent> ${item.productName}'
                                  : item.productName,
                              style: pw.TextStyle(font: font, fontSize: 8))),
                      pw.Text(lineTotal,
                          style: pw.TextStyle(font: font, fontSize: 8)),
                    ],
                  ),
                  pw.Text(
                    '$indent  ${item.quantity} x ${money(item.unitPrice)}',
                    style: pw.TextStyle(font: font, fontSize: 7),
                  ),
                  ...item.options.map((o) => pw.Text(
                        '$indent  + ${o.optionName}  ${money(o.priceAdjustment)}',
                        style: pw.TextStyle(font: font, fontSize: 7),
                      )),
                  ...item.addons.map((a) => pw.Text(
                        a.wasRemoved
                            ? '$indent  - No ${a.name}'
                            : '$indent  + ${a.name}  ${money(a.priceDelta)}',
                        style: pw.TextStyle(font: font, fontSize: 7),
                      )),
                ],
              ),
            );
          }),

          pw.Divider(thickness: 0.5),

          // Totals
          _row('Subtotal', money(receipt.subtotal),
              font: font, boldFont: boldFont),
          if ((double.tryParse(receipt.discount) ?? 0) > 0)
            _row('Discount', '-${money(receipt.discount)}',
                font: font, boldFont: boldFont),
          if ((double.tryParse(receipt.taxAmount) ?? 0) > 0)
            _row('Tax', money(receipt.taxAmount),
                font: font, boldFont: boldFont),
          _row('TOTAL', money(receipt.total),
              font: font, boldFont: boldFont, highlight: true),

          pw.Divider(thickness: 0.5),

          // Payments
          ...receipt.payments.map((p) => _row(
                p.paymentMethod,
                money(p.amount),
                font: font,
                boldFont: boldFont,
              )),
          if ((double.tryParse(receipt.change) ?? 0) > 0)
            _row('Change', money(receipt.change),
                font: font, boldFont: boldFont),

          pw.SizedBox(height: 8),
          pw.Center(
            child: pw.Text(
                receipt.receiptThankYou?.isNotEmpty == true
                    ? receipt.receiptThankYou!
                    : 'Thank you!',
                style: pw.TextStyle(font: font, fontSize: 8)),
          ),
          if (receipt.receiptTerms?.isNotEmpty ?? false) ...[
            pw.SizedBox(height: 5),
            pw.Divider(thickness: 0.5),
            pw.Center(
                child: pw.Text(receipt.receiptTerms!,
                    textAlign: pw.TextAlign.center,
                    style: pw.TextStyle(font: font, fontSize: 6))),
          ],
          pw.SizedBox(height: 6),
          pw.Center(
            child: pw.Text(
                'Storixx - developed by apkaysoftware.com - 03487457766',
                textAlign: pw.TextAlign.center,
                style: pw.TextStyle(font: font, fontSize: 5)),
          ),
        ],
      ),
    ));

    return doc;
  }

  /// Sends the receipt PDF directly to a system printer.
  Future<void> printReceipt(PosReceiptResponse receipt,
      {ReceiptPrintLayout layout = ReceiptPrintLayout.a4}) async {
    final doc = await generateReceipt(receipt, layout: layout);
    await Printing.layoutPdf(onLayout: (_) => doc.save());
  }

  /// Opens the share sheet so the cashier can email or share the receipt PDF.
  Future<void> shareReceipt(PosReceiptResponse receipt,
      {ReceiptPrintLayout layout = ReceiptPrintLayout.a4}) async {
    final doc = await generateReceipt(receipt, layout: layout);
    await Printing.sharePdf(
      bytes: await doc.save(),
      filename: 'receipt_${receipt.saleNumber}.pdf',
    );
  }

  Future<pw.Document> generateShiftSummary(
      SessionSummaryResponse response) async {
    final doc = pw.Document();
    final font = pw.Font.helvetica();
    final bold = pw.Font.helveticaBold();
    final session = response.session;
    final summary = response.summary;

    pw.Widget line(String label, String value, {bool strong = false}) =>
        pw.Padding(
          padding: const pw.EdgeInsets.symmetric(vertical: 3),
          child: pw.Row(
            mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
            children: [
              pw.Text(label,
                  style:
                      pw.TextStyle(font: strong ? bold : font, fontSize: 10)),
              pw.Text(value,
                  style:
                      pw.TextStyle(font: strong ? bold : font, fontSize: 10)),
            ],
          ),
        );

    String money(String value) =>
        _moneyFormat.format(double.tryParse(value) ?? 0);

    doc.addPage(pw.MultiPage(
      pageFormat: PdfPageFormat.a4,
      margin: const pw.EdgeInsets.all(28),
      build: (_) => [
        pw.Text('STORIXX - SHIFT SUMMARY',
            style: pw.TextStyle(font: bold, fontSize: 16)),
        pw.SizedBox(height: 10),
        line('Shift', session.shiftNumber ?? session.id),
        line('Opened', _dateFormat.format(session.openedAt.toLocal())),
        if (session.closedAt != null)
          line('Closed', _dateFormat.format(session.closedAt!.toLocal())),
        pw.Divider(),
        line('Opening cash', money(summary.openingCash)),
        line('Completed sales', '${summary.salesCount}'),
        line('Subtotal / gross sales', money(summary.subtotalTotal)),
        line('Discounts', '-${money(summary.discountTotal)}'),
        line('Tax', money(summary.taxTotal)),
        line('Sales total', money(summary.grossTotal), strong: true),
        pw.SizedBox(height: 8),
        pw.Text('PAYMENTS RECEIVED',
            style: pw.TextStyle(font: bold, fontSize: 11)),
        ...summary.byPaymentMethod.entries
            .map((entry) => line(entry.key, money(entry.value))),
        line('All payments', money(summary.totalPayments), strong: true),
        pw.SizedBox(height: 8),
        pw.Text('REFUNDS', style: pw.TextStyle(font: bold, fontSize: 11)),
        line('Refund count', '${summary.refundsCount}'),
        ...summary.refundsByPaymentMethod.entries
            .where((entry) => (double.tryParse(entry.value) ?? 0) != 0)
            .map((entry) => line(entry.key, '-${money(entry.value)}')),
        line('All refunds', '-${money(summary.refundTotal)}', strong: true),
        pw.SizedBox(height: 8),
        pw.Text('CANCELLED BILLS',
            style: pw.TextStyle(font: bold, fontSize: 11)),
        line('Cancellation count', '${summary.cancellationsCount}'),
        ...summary.cancellationsByPaymentMethod.entries
            .where((entry) => (double.tryParse(entry.value) ?? 0) != 0)
            .map((entry) => line(entry.key, money(entry.value))),
        line('Cancelled bill total', money(summary.cancellationTotal),
            strong: true),
        pw.Divider(),
        line('Net sales after refunds', money(summary.netTotal), strong: true),
        line('Expected cash in drawer', money(summary.expectedCash),
            strong: true),
        if (session.closingCash != null)
          line('Counted cash', money(session.closingCash!), strong: true),
      ],
    ));
    return doc;
  }

  Future<void> printShiftSummary(SessionSummaryResponse response) async {
    final doc = await generateShiftSummary(response);
    await Printing.layoutPdf(onLayout: (_) => doc.save());
  }

  Future<void> shareShiftSummary(SessionSummaryResponse response) async {
    final doc = await generateShiftSummary(response);
    await Printing.sharePdf(
      bytes: await doc.save(),
      filename: 'shift_${response.session.shiftNumber ?? response.session.id}.pdf',
    );
  }

  /// Opens the operating-system printer dialog with a harmless diagnostic
  /// page. Windows laser/inkjet printers and Android print-service printers
  /// (including supported paired Bluetooth models) appear there.
  Future<void> printTestPage(
      {ReceiptPrintLayout layout = ReceiptPrintLayout.a4}) async {
    final doc = pw.Document()
      ..addPage(pw.Page(
        pageFormat: layout == ReceiptPrintLayout.thermal80
            ? const PdfPageFormat(80 * PdfPageFormat.mm, 100 * PdfPageFormat.mm,
                marginAll: 4 * PdfPageFormat.mm)
            : PdfPageFormat.a4,
        build: (_) => pw.Center(
          child: pw.Column(mainAxisSize: pw.MainAxisSize.min, children: [
            pw.Text('STORIXX',
                style:
                    pw.TextStyle(font: pw.Font.helveticaBold(), fontSize: 22)),
            pw.SizedBox(height: 12),
            pw.Text('Printer test successful',
                style: pw.TextStyle(font: pw.Font.helvetica(), fontSize: 13)),
            pw.Text(_dateFormat.format(DateTime.now()),
                style: pw.TextStyle(font: pw.Font.helvetica(), fontSize: 10)),
          ]),
        ),
      ));
    await Printing.layoutPdf(onLayout: (_) => doc.save());
  }

  pw.Widget _row(
    String label,
    String value, {
    required pw.Font font,
    required pw.Font boldFont,
    bool highlight = false,
  }) =>
      pw.Row(
        mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
        children: [
          pw.Text(label,
              style:
                  pw.TextStyle(font: highlight ? boldFont : font, fontSize: 8)),
          pw.Text(value,
              style:
                  pw.TextStyle(font: highlight ? boldFont : font, fontSize: 8)),
        ],
      );
}
