import 'package:drift/drift.dart';
import '../app_database.dart';
import '../tables/app_settings_table.dart';

part 'settings_dao.g.dart';

/// DAO for reading and writing persistent key-value application settings.
///
/// Provides typed accessors for the two critical settings used by sync and
/// sale-number generation, plus a generic [get]/[set] pair for future keys.
@DriftAccessor(tables: [AppSettingsTable])
class SettingsDao extends DatabaseAccessor<AppDatabase>
    with _$SettingsDaoMixin {
  SettingsDao(super.db);

  static const _lastSyncKey = 'last_sync_at';
  static const _saleCounterKey = 'sale_counter';

  // ── Activation (business + branch), persisted once ───────────────────────
  static const _businessIdKey = 'business_id';
  static const _businessNameKey = 'business_name';
  static const _branchIdKey = 'branch_id';
  static const _branchNameKey = 'branch_name';
  static const _deviceLetterKey = 'device_letter';
  static const _currencyKey = 'currency';
  static const _lowStockThresholdKey = 'low_stock_threshold';
  static const _posLayoutKey = 'pos_layout';
  static const _branchCodeKey = 'branch_code';
  static const _branchAddressKey = 'branch_address';
  static const _branchPhoneKey = 'branch_phone';
  static const _receiptLogoKey = 'receipt_logo_base64';
  static const _receiptTaglineKey = 'receipt_tagline';
  static const _receiptThankYouKey = 'receipt_thank_you';
  static const _receiptTermsKey = 'receipt_terms';
  static const _receiptPrintLayoutKey = 'receipt_print_layout';
  static const _bluetoothPrinterAddressKey = 'bluetooth_printer_address';
  static const _bluetoothPrinterNameKey = 'bluetooth_printer_name';
  static const _thermalPrintTransportKey = 'thermal_print_transport';

  /// Returns the stored value for [key], or null if the key does not exist.
  Future<String?> get(String key) async {
    final row = await (select(appSettingsTable)
          ..where((t) => t.key.equals(key)))
        .getSingleOrNull();
    return row?.value;
  }

  Stream<String?> watchValue(String key) =>
      (select(appSettingsTable)..where((t) => t.key.equals(key)))
          .watchSingleOrNull()
          .map((row) => row?.value);

  /// Writes [value] for [key], replacing any existing value (upsert).
  Future<void> set(String key, String value) =>
      into(appSettingsTable).insertOnConflictUpdate(
        AppSettingsTableCompanion.insert(key: key, value: value),
      );

  /// Returns the timestamp of the last successful sync, or null on first launch.
  ///
  /// Used by [SyncRepository.deltaSync] as the `since` cursor sent to the server.
  Future<DateTime?> getLastSyncAt() async {
    final v = await get(_lastSyncKey);
    return v != null ? DateTime.parse(v) : null;
  }

  /// Persists [dt] as the new last-sync cursor after a successful sync.
  ///
  /// Stored as UTC ISO-8601 so it can be compared directly with server timestamps.
  Future<void> setLastSyncAt(DateTime dt) =>
      set(_lastSyncKey, dt.toUtc().toIso8601String());

  // ── Activation accessors ──────────────────────────────────────────────────

  /// Persists the business + branch context returned by device activation.
  ///
  /// Called once from the activation screen. `isOnboarded` returns true
  /// afterwards and the app skips straight to the staff picker on next launch.
  Future<void> saveOnboarding({
    required String businessId,
    required String businessName,
    required String branchId,
    required String branchName,
    required String currency,
    required String deviceLetter,
  }) async {
    await set(_businessIdKey, businessId);
    await set(_businessNameKey, businessName);
    await set(_branchIdKey, branchId);
    await set(_branchNameKey, branchName);
    await set(_currencyKey, currency);
    await set(_deviceLetterKey, deviceLetter);
  }

  /// Wipes activation state — used by "Deactivate this device".
  Future<void> clearOnboarding() async {
    for (final k in [
      _businessIdKey,
      _businessNameKey,
      _branchIdKey,
      _branchNameKey,
      _currencyKey,
      _deviceLetterKey,
    ]) {
      await (delete(appSettingsTable)..where((t) => t.key.equals(k))).go();
    }
  }

  Future<String?> getBusinessId() => get(_businessIdKey);
  Future<String?> getBusinessName() => get(_businessNameKey);
  Future<String?> getBranchId() => get(_branchIdKey);
  Future<String?> getBranchName() => get(_branchNameKey);
  Future<String?> getBranchCode() => get(_branchCodeKey);
  Future<String?> getDeviceLetter() => get(_deviceLetterKey);
  Future<String?> getBranchAddress() => get(_branchAddressKey);
  Future<String?> getBranchPhone() => get(_branchPhoneKey);
  Future<String?> getReceiptLogoBase64() => get(_receiptLogoKey);
  Future<String?> getReceiptTagline() => get(_receiptTaglineKey);
  Future<String?> getReceiptThankYou() => get(_receiptThankYouKey);
  Future<String?> getReceiptTerms() => get(_receiptTermsKey);

  /// Paper used for both the system print dialog and exported/shared PDFs.
  /// Existing installations default to A4 until the cashier selects 80 mm.
  Future<String> getReceiptPrintLayout() async =>
      (await get(_receiptPrintLayoutKey)) ?? 'a4';

  Future<void> setReceiptPrintLayout(String value) {
    if (value != 'a4' && value != 'thermal80') {
      throw ArgumentError.value(value, 'value', 'Unsupported receipt layout');
    }
    return set(_receiptPrintLayoutKey, value);
  }

  Future<String?> getBluetoothPrinterAddress() =>
      get(_bluetoothPrinterAddressKey);
  Future<String?> getBluetoothPrinterName() => get(_bluetoothPrinterNameKey);

  Future<void> saveBluetoothPrinter({
    required String address,
    required String name,
  }) async {
    await set(_bluetoothPrinterAddressKey, address);
    await set(_bluetoothPrinterNameKey, name);
  }

  Future<void> clearBluetoothPrinter() async {
    for (final key in [
      _bluetoothPrinterAddressKey,
      _bluetoothPrinterNameKey,
    ]) {
      await (delete(appSettingsTable)..where((t) => t.key.equals(key))).go();
    }
  }

  /// `bluetooth` sends ESC/POS bytes directly; `system` uses the OS driver.
  Future<String> getThermalPrintTransport() async =>
      (await get(_thermalPrintTransportKey)) ?? 'bluetooth';

  Future<void> setThermalPrintTransport(String value) {
    if (value != 'bluetooth' && value != 'system') {
      throw ArgumentError.value(value, 'value', 'Unsupported print transport');
    }
    return set(_thermalPrintTransportKey, value);
  }

  Future<void> saveReceiptProfile({
    required String businessName,
    required String branchName,
    required String branchCode,
    String? branchAddress,
    String? branchPhone,
    String? logoBase64,
    String? tagline,
    String? thankYou,
    String? terms,
  }) async {
    await set(_businessNameKey, businessName);
    await set(_branchNameKey, branchName);
    await set(_branchCodeKey, branchCode);
    await _setOptional(_branchAddressKey, branchAddress);
    await _setOptional(_branchPhoneKey, branchPhone);
    await _setOptional(_receiptLogoKey, logoBase64);
    await _setOptional(_receiptTaglineKey, tagline);
    await _setOptional(_receiptThankYouKey, thankYou);
    await _setOptional(_receiptTermsKey, terms);
  }

  Future<void> _setOptional(String key, String? value) async {
    if (value == null || value.isEmpty) {
      await (delete(appSettingsTable)..where((t) => t.key.equals(key))).go();
    } else {
      await set(key, value);
    }
  }

  /// Money display string synced from the cloud; defaults to "Rs." when unset.
  Future<String> getCurrency() async => (await get(_currencyKey)) ?? 'Rs.';

  /// Persists the currency string from a full sync payload.
  Future<void> setCurrency(String value) => set(_currencyKey, value);

  Future<int> getLowStockThreshold() async =>
      int.tryParse((await get(_lowStockThresholdKey)) ?? '') ?? 5;

  Future<void> setLowStockThreshold(int value) =>
      set(_lowStockThresholdKey, value < 0 ? '0' : value.toString());

  /// POS layout ('grid_with_variant_picker' or 'grid_quick_tap') driven by
  /// the tenant's Business Template (spec Part C / F3/G4), synced from the
  /// cloud so it's available offline. Defaults to the side-panel layout —
  /// the only layout that existed before this config was introduced.
  Future<String> getPosLayout() async =>
      (await get(_posLayoutKey)) ?? 'grid_with_variant_picker';

  /// Persists the POS layout string from a full sync payload.
  Future<void> setPosLayout(String value) => set(_posLayoutKey, value);

  /// True once a Shop ID has been validated and a branch chosen.
  Future<bool> isOnboarded() async => (await get(_branchIdKey)) != null;

  /// Atomically increments and returns the sale counter.
  ///
  /// The returned integer is used to build the human-readable sale number
  /// (e.g. "LHR01-B-26-000128" — branch code, device letter, year, counter).
  /// The counter persists across app restarts so numbers are never reused
  /// within a device's lifetime. It is device-local and NOT device-unique by
  /// itself — the device letter folded into the number is what keeps two
  /// devices at the same branch from ever generating the same sale_number.
  Future<int> nextSaleCounter() async {
    final v = await get(_saleCounterKey);
    final next = (int.tryParse(v ?? '0') ?? 0) + 1;
    await set(_saleCounterKey, next.toString());
    return next;
  }
}
