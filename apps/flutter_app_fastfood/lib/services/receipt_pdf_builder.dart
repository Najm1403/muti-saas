import 'dart:convert';

import 'package:intl/intl.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;

import '../core/models/sale/pos_receipt_item.dart';
import '../core/models/sale/pos_receipt_response.dart';

class ReceiptPdfBuilder {
  static final _date = DateFormat('dd MMM yyyy HH:mm');
  static final _number = NumberFormat('#,##0.00');

  static Future<pw.Document> build(PosReceiptResponse receipt) async {
    final doc = pw.Document();
    final font = pw.Font.helvetica();
    final bold = pw.Font.helveticaBold();
    final navy = PdfColor.fromHex('#102A56');
    pw.MemoryImage? logo;
    if (receipt.receiptLogoBase64?.isNotEmpty ?? false) {
      try {
        logo = pw.MemoryImage(base64Decode(receipt.receiptLogoBase64!));
      } catch (_) {
        // A damaged cached logo must never prevent a receipt from printing.
      }
    }
    String money(String value) =>
        '${receipt.currency} ${_number.format(double.tryParse(value) ?? 0)}';
    final items = groupReceiptItemsForDisplay(receipt.items);

    doc.addPage(pw.MultiPage(
      pageFormat: PdfPageFormat.a4,
      margin: const pw.EdgeInsets.all(34),
      theme: pw.ThemeData.withFont(base: font, bold: bold),
      build: (_) => [
        pw.Row(crossAxisAlignment: pw.CrossAxisAlignment.center, children: [
          if (logo != null) ...[
            pw.SizedBox(
                width: 82,
                height: 58,
                child: pw.Image(logo, fit: pw.BoxFit.contain)),
            pw.SizedBox(width: 16),
          ],
          pw.Expanded(
              child: pw.Column(
                  crossAxisAlignment: pw.CrossAxisAlignment.start,
                  children: [
                pw.Text(
                    receipt.businessName.isEmpty
                        ? receipt.branchName
                        : receipt.businessName,
                    style: pw.TextStyle(font: bold, fontSize: 25, color: navy)),
                if (receipt.receiptTagline?.isNotEmpty ?? false)
                  pw.Text(receipt.receiptTagline!,
                      style: const pw.TextStyle(
                          fontSize: 10,
                          letterSpacing: 1.4,
                          color: PdfColors.blueGrey600)),
              ])),
        ]),
        pw.Divider(height: 28, color: PdfColors.blueGrey200),
        if (receipt.status != 'COMPLETED')
          pw.Container(
              margin: const pw.EdgeInsets.only(bottom: 10),
              padding:
                  const pw.EdgeInsets.symmetric(horizontal: 10, vertical: 5),
              decoration: pw.BoxDecoration(
                  color: PdfColors.red50,
                  border: pw.Border.all(color: PdfColors.red200),
                  borderRadius: pw.BorderRadius.circular(4)),
              child: pw.Text(receipt.status,
                  style: pw.TextStyle(
                      font: bold, fontSize: 11, color: PdfColors.red700))),
        pw.Row(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
          pw.Expanded(
              child: pw.Column(
                  crossAxisAlignment: pw.CrossAxisAlignment.start,
                  children: [
                pw.Text(
                    '${receipt.branchName}${receipt.branchCode.isEmpty ? '' : ' (${receipt.branchCode})'}',
                    style: pw.TextStyle(font: bold, fontSize: 12, color: navy)),
                if (receipt.branchAddress?.isNotEmpty ?? false)
                  pw.Text(receipt.branchAddress!,
                      style: const pw.TextStyle(fontSize: 10)),
                if (receipt.branchPhone?.isNotEmpty ?? false)
                  pw.Text('Ph: ${receipt.branchPhone}',
                      style: const pw.TextStyle(fontSize: 10)),
              ])),
          pw.Expanded(
              child: pw.Column(
                  crossAxisAlignment: pw.CrossAxisAlignment.start,
                  children: [
                _meta('Receipt #', receipt.saleNumber, bold),
                _meta('Date & Time', _date.format(receipt.soldAt.toLocal()),
                    bold),
                _meta('Cashier', receipt.cashierName, bold),
              ])),
        ]),
        pw.SizedBox(height: 24),
        pw.TableHelper.fromTextArray(
          headers: const ['#', 'ITEM', 'QTY', 'UNIT PRICE', 'AMOUNT'],
          data: [
            for (var i = 0; i < items.length; i++)
              [
                '${i + 1}',
                _itemLabel(items[i], money),
                items[i].quantity,
                money(items[i].unitPrice),
                money(items[i].total),
              ]
          ],
          headerDecoration: const pw.BoxDecoration(color: PdfColors.blueGrey50),
          headerStyle: pw.TextStyle(font: bold, color: navy, fontSize: 9),
          cellStyle: const pw.TextStyle(fontSize: 9),
          cellPadding:
              const pw.EdgeInsets.symmetric(horizontal: 7, vertical: 9),
          border: const pw.TableBorder(
              horizontalInside:
                  pw.BorderSide(color: PdfColors.blueGrey100, width: .5)),
          columnWidths: {
            0: const pw.FixedColumnWidth(24),
            1: const pw.FlexColumnWidth(3),
            2: const pw.FlexColumnWidth(1),
            3: const pw.FlexColumnWidth(1.4),
            4: const pw.FlexColumnWidth(1.4),
          },
          cellAlignments: {
            2: pw.Alignment.centerRight,
            3: pw.Alignment.centerRight,
            4: pw.Alignment.centerRight,
          },
        ),
        pw.SizedBox(height: 14),
        pw.Align(
            alignment: pw.Alignment.centerRight,
            child: pw.SizedBox(
                width: 250,
                child: pw.Column(children: [
                  _total('Subtotal', money(receipt.subtotal), bold),
                  if ((double.tryParse(receipt.discount) ?? 0) > 0)
                    _total('Discount', '-${money(receipt.discount)}', bold),
                  if ((double.tryParse(receipt.taxAmount) ?? 0) > 0)
                    _total('Tax', money(receipt.taxAmount), bold),
                  pw.Container(
                      margin: const pw.EdgeInsets.only(top: 5),
                      padding: const pw.EdgeInsets.all(10),
                      color: PdfColors.blue50,
                      child: _total('TOTAL', money(receipt.total), bold,
                          strong: true)),
                ]))),
        pw.SizedBox(height: 14),
        pw.Container(
            padding: const pw.EdgeInsets.all(12),
            decoration: pw.BoxDecoration(
                color: PdfColors.grey100,
                borderRadius: pw.BorderRadius.circular(5)),
            child: pw.Column(children: [
              for (final payment in receipt.payments)
                _total('Payment - ${payment.paymentMethod}',
                    money(payment.amount), bold),
              if ((double.tryParse(receipt.change) ?? 0) > 0)
                _total('Change', money(receipt.change), bold),
            ])),
        pw.SizedBox(height: 28),
        pw.Center(
            child: pw.Column(children: [
          pw.Text(
              receipt.receiptThankYou?.isNotEmpty == true
                  ? receipt.receiptThankYou!
                  : 'THANK YOU!',
              style: pw.TextStyle(
                  font: bold, fontSize: 17, color: navy, letterSpacing: 2)),
          if (receipt.businessName.isNotEmpty)
            pw.Text('For shopping with ${receipt.businessName}',
                style: const pw.TextStyle(
                    fontSize: 10, color: PdfColors.blueGrey600)),
        ])),
        if (receipt.receiptTerms?.isNotEmpty ?? false) ...[
          pw.SizedBox(height: 22),
          pw.Divider(color: PdfColors.blueGrey200),
          pw.Center(
              child: pw.Text(receipt.receiptTerms!,
                  textAlign: pw.TextAlign.center,
                  style: const pw.TextStyle(
                      fontSize: 8, color: PdfColors.blueGrey600))),
        ],
        pw.SizedBox(height: 10),
        pw.Center(
            child: pw.Text(
                'Storixx · developed by apkaysoftware.com · 03487457766',
                textAlign: pw.TextAlign.center,
                style: const pw.TextStyle(
                    fontSize: 7, color: PdfColors.blueGrey400))),
      ],
    ));
    return doc;
  }

  static pw.Widget _meta(String label, String value, pw.Font bold) =>
      pw.Padding(
          padding: const pw.EdgeInsets.only(bottom: 4),
          child: pw.RichText(
              text: pw.TextSpan(children: [
            pw.TextSpan(
                text: '$label: ',
                style: pw.TextStyle(font: bold, fontSize: 10)),
            pw.TextSpan(text: value, style: const pw.TextStyle(fontSize: 10)),
          ])));

  static pw.Widget _total(String label, String value, pw.Font bold,
          {bool strong = false}) =>
      pw.Row(mainAxisAlignment: pw.MainAxisAlignment.spaceBetween, children: [
        pw.Text(label,
            style: pw.TextStyle(
                font: strong ? bold : null, fontSize: strong ? 13 : 10)),
        pw.Text(value,
            style: pw.TextStyle(
                font: strong ? bold : null, fontSize: strong ? 13 : 10)),
      ]);

  static String _itemLabel(PosReceiptItem item, String Function(String) money) {
    final options = item.options
        .map((option) => option.optionName)
        .where((name) => name.isNotEmpty);
    final addons = item.addons.map((addon) {
      if (addon.wasRemoved) return 'No ${addon.name}';
      final delta = double.tryParse(addon.priceDelta) ?? 0;
      return delta > 0 ? '${addon.name} (${money(addon.priceDelta)})' : addon.name;
    });
    final extras = [...options, ...addons].join(', ');
    final prefix = item.parentItemId == null ? '' : '- ';
    return '$prefix${item.productName}${extras.isEmpty ? '' : '\n$extras'}';
  }
}
