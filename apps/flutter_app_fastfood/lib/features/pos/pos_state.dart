import '../../providers/auth_notifier.dart';
// features/pos/pos_state.dart
//
// State management for the POS order-picker screen.
//
// Architecture:
//   • PosState / PosNotifier    — UI selection state (no codegen; keepAlive via StateNotifierProvider)
//   • DraftOrder / DraftNotifier — in-memory parked orders, scoped to the current cashier
//   • ticketCounterProvider     — monotonic ticket number per session

import 'package:decimal/decimal.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';

import '../sale/cart_service.dart';

// ---------------------------------------------------------------------------
// DraftOrder — parked order snapshot
// ---------------------------------------------------------------------------

/// A named snapshot of the cart that has been "parked" and can be resumed later.
///
/// Drafts are held entirely in memory. They are lost when the app restarts —
/// this is intentional for V1; a future version could persist them to SQLite.
class DraftOrder {
  /// Unique ID (UUID v4) generated when the draft is created.
  final String id;

  /// Human-readable label shown in the drafts overlay, e.g. "Ticket #1002".
  final String label;

  /// Immutable snapshot of cart items at the time the order was parked.
  final List<CartItem> items;

  /// Tax rate active at park time, so the resumed cart uses the same config.
  final Decimal taxRate;

  /// Whether tax was inclusive in product prices at park time.
  final bool taxInclusive;

  /// Wall-clock timestamp when the draft was created.
  final DateTime createdAt;

  const DraftOrder({
    required this.id,
    required this.label,
    required this.items,
    required this.taxRate,
    required this.taxInclusive,
    required this.createdAt,
  });
}

// ---------------------------------------------------------------------------
// PosOverlay — which full-screen overlay panel is open
// ---------------------------------------------------------------------------

/// Which slide-in overlay is currently visible over the POS screen.
///
/// [none]   — default; catalog + variant panel are fully interactive.
/// [cart]   — cart review panel (460 px from right edge).
/// [drafts] — parked draft orders panel (same size as cart).
enum PosOverlay { none, cart, drafts }

// ---------------------------------------------------------------------------
// PosState — immutable UI selection snapshot
// ---------------------------------------------------------------------------

/// Immutable snapshot of every piece of UI state the POS screen needs.
///
/// All changes go through [PosNotifier] methods — widgets never mutate
/// fields directly. This keeps state transitions centralized and testable.
///
/// [selectedVariantOptions] and [selectedAddons] are two structurally
/// separate maps (spec F1) — never one map standing in for both concepts.
class PosState {
  /// ID of the selected category tile (Step 1). Null before any tap.
  final String? selectedCategoryId;

  /// ID of the selected product card (Step 2). Null before any tap.
  final String? selectedProductId;

  /// Variant Option selections: groupId -> ONE optionId (single-select, always).
  final Map<String, String> selectedVariantOptions;

  /// Add-on selections: addonGroupId -> Set of addonItemIds (multi-select).
  final Map<String, Set<String>> selectedAddons;

  /// Inventory Component selections: groupId -> ONE optionId (single-select,
  /// same shape as [selectedVariantOptions] — max_selections > 1 is a future
  /// extension, not needed for the common "one RAM stick" case). Laptop
  /// Store shareable-inventory model — kept structurally separate from both
  /// maps above since a component resolves to its OWN Variant/price/stock,
  /// unlike either a specification value or an Add-on.
  final Map<String, String> selectedComponents;

  /// Units of the current product to add. Always ≥ 1.
  final int quantity;

  /// Which overlay is currently open.
  final PosOverlay overlay;

  /// Non-null while a toast message is visible; cleared by [PosNotifier.clearToast].
  final String? toast;

  /// Free-text product search (name / product code / Variant Selection
  /// group or option name). Empty string means "not searching" — the
  /// product grid falls back to the category-filtered listing.
  final String searchQuery;

  const PosState({
    this.selectedCategoryId,
    this.selectedProductId,
    this.selectedVariantOptions = const {},
    this.selectedAddons = const {},
    this.selectedComponents = const {},
    this.quantity = 1,
    this.overlay = PosOverlay.none,
    this.toast,
    this.searchQuery = '',
  });

  /// Returns a copy of this state with the specified fields replaced.
  ///
  /// Uses [_keep] sentinels for nullable fields so callers can explicitly
  /// set them to null without ambiguity.
  PosState copyWith({
    String? selectedCategoryId,
    String? selectedProductId,
    Object? selectedVariantOptions = _keep,
    Object? selectedAddons = _keep,
    Object? selectedComponents = _keep,
    int? quantity,
    PosOverlay? overlay,
    Object? toast = _keep,
    String? searchQuery,
  }) {
    Map<String, String> stringMap(Object? value) {
      if (value == null) return <String, String>{};
      final map = value as Map;
      return <String, String>{
        for (final entry in map.entries)
          entry.key.toString(): entry.value.toString(),
      };
    }

    Map<String, Set<String>> stringSetMap(Object? value) {
      if (value == null) return <String, Set<String>>{};
      final map = value as Map;
      return <String, Set<String>>{
        for (final entry in map.entries)
          entry.key.toString():
              (entry.value as Iterable).map((item) => item.toString()).toSet(),
      };
    }

    final nextVariantOptions = identical(selectedVariantOptions, _keep)
        ? this.selectedVariantOptions
        : stringMap(selectedVariantOptions);
    final nextAddons = identical(selectedAddons, _keep)
        ? this.selectedAddons
        : stringSetMap(selectedAddons);
    final nextComponents = identical(selectedComponents, _keep)
        ? this.selectedComponents
        : stringMap(selectedComponents);
    return PosState(
      selectedCategoryId: selectedCategoryId ?? this.selectedCategoryId,
      selectedProductId: selectedProductId ?? this.selectedProductId,
      selectedVariantOptions: nextVariantOptions,
      selectedAddons: nextAddons,
      selectedComponents: nextComponents,
      quantity: quantity ?? this.quantity,
      overlay: overlay ?? this.overlay,
      toast: identical(toast, _keep) ? this.toast : toast as String?,
      searchQuery: searchQuery ?? this.searchQuery,
    );
  }
}

// Sentinel object used in copyWith to distinguish "not provided" from explicit null.
const _keep = Object();

// ---------------------------------------------------------------------------
// PosNotifier — all POS UI state transitions
// ---------------------------------------------------------------------------

/// Manages all state transitions for the POS order-picker screen.
///
/// One instance lives for the session lifetime (keepAlive on the provider).
/// Every public method corresponds to a concrete cashier action on screen,
/// making transitions easy to read and unit-test independently.
class PosNotifier extends StateNotifier<PosState> {
  PosNotifier() : super(const PosState());

  // ── Step 1: category selection ───────────────────────────────────────────

  /// Selects [categoryId] and clears any previously selected product.
  ///
  /// Changing category resets the customization panel (Steps 3-4) so stale
  /// selections from the previous product are never shown.
  void selectCategory(String categoryId) {
    state = PosState(
      selectedCategoryId: categoryId,
      overlay: state.overlay, // preserve overlay visibility
      searchQuery: state.searchQuery, // preserve in-progress search text
    );
  }

  // ── Step 2: product selection ────────────────────────────────────────────

  /// Selects [productId] and resets variant/add-on/quantity state to defaults.
  ///
  /// Opens the customization panel with a clean slate for the newly chosen product.
  void selectProduct(String productId) {
    state = PosState(
      selectedCategoryId: state.selectedCategoryId,
      selectedProductId: productId,
      selectedVariantOptions: <String, String>{},
      selectedAddons: <String, Set<String>>{},
      selectedComponents: <String, String>{},
      quantity: 1,
      overlay: state.overlay,
      searchQuery: state.searchQuery,
    );
  }

  /// Deselects the current product and collapses the customization panel.
  void clearProduct() {
    state = state.copyWith(
      selectedProductId: null,
      selectedVariantOptions: {},
      selectedAddons: {},
      selectedComponents: {},
      quantity: 1,
    );
  }

  // ── Step 3a: Variant Option selection (radio, one per group) ────────────

  /// Selects [optionId] within Variant Option Group [groupId].
  ///
  /// Radio behavior: selecting replaces any prior selection in that group;
  /// re-tapping the same option clears it (spec F1).
  void selectVariantOption(String groupId, String optionId) {
    final existing = Map<String, String>.from(state.selectedVariantOptions);
    if (existing[groupId] == optionId) {
      existing.remove(groupId);
    } else {
      existing[groupId] = optionId;
    }
    state = state.copyWith(selectedVariantOptions: existing);
  }

  // ── Step 3a½: Inventory Component selection (radio, one per group) ──────

  /// Selects [optionId] within Component Group [groupId] (Laptop Store
  /// shareable-inventory model — RAM, Storage, ...). Same radio behavior as
  /// [selectVariantOption]: selecting replaces any prior pick in that group,
  /// re-tapping the same option clears it.
  void selectComponentOption(String groupId, String optionId) {
    final existing = Map<String, String>.from(state.selectedComponents);
    if (existing[groupId] == optionId) {
      existing.remove(groupId);
    } else {
      existing[groupId] = optionId;
    }
    state = state.copyWith(selectedComponents: existing);
  }

  // ── Step 3b: Add-on toggling (checkbox, respects maxSelections) ─────────

  /// Toggles [addonItemId] within Add-on Group [groupId].
  ///
  /// Checkbox behavior: adds/removes from the set, respecting [maxSelections]
  /// if given (spec F1).
  void toggleAddon(String groupId, String addonItemId, {int? maxSelections}) {
    final existing = Map<String, Set<String>>.from(state.selectedAddons);
    final groupSet = Set<String>.from(existing[groupId] ?? {});
    if (groupSet.contains(addonItemId)) {
      groupSet.remove(addonItemId);
    } else {
      if (maxSelections != null && groupSet.length >= maxSelections) return;
      groupSet.add(addonItemId);
    }
    existing[groupId] = groupSet;
    state = state.copyWith(selectedAddons: existing);
  }

  /// Merges [defaults] (addonGroupId -> default-selected item ids) into the
  /// current selection, without overwriting a group the cashier already
  /// touched. Called once per product when its Add-on Groups first load, so
  /// `default_selected` items start checked (spec F4).
  void seedDefaultAddons(Map<String, Set<String>> defaults) {
    final existing = Map<String, Set<String>>.from(state.selectedAddons);
    var changed = false;
    for (final entry in defaults.entries) {
      if (!existing.containsKey(entry.key)) {
        existing[entry.key] = entry.value;
        changed = true;
      }
    }
    if (changed) state = state.copyWith(selectedAddons: existing);
  }

  // ── Step 4: quantity stepper ─────────────────────────────────────────────

  /// Increments quantity by 1 (no upper cap for V1).
  void incrementQty() => state = state.copyWith(quantity: state.quantity + 1);

  /// Decrements quantity by 1; clamped at minimum of 1.
  void decrementQty() {
    if (state.quantity > 1) {
      state = state.copyWith(quantity: state.quantity - 1);
    }
  }

  // ── Product search ────────────────────────────────────────────────────────

  /// Updates the free-text product search query.
  ///
  /// An empty [query] returns the grid to the category-filtered listing.
  /// Does not touch category/product selection — the cashier may still tap
  /// a result while a search is active.
  void setSearchQuery(String query) =>
      state = state.copyWith(searchQuery: query);

  // ── Overlay panels ───────────────────────────────────────────────────────

  /// Opens the cart review panel (slides in from right edge).
  void openCart() => state = state.copyWith(overlay: PosOverlay.cart);

  /// Opens the draft orders panel.
  void openDrafts() => state = state.copyWith(overlay: PosOverlay.drafts);

  /// Closes any open overlay and returns to the normal POS layout.
  void closeOverlay() => state = state.copyWith(overlay: PosOverlay.none);

  // ── Toast notification ───────────────────────────────────────────────────

  /// Shows [message] in the centered bottom toast.
  ///
  /// [PosToast] widget schedules [clearToast] automatically after its
  /// display duration expires.
  void showToast(String message) => state = state.copyWith(toast: message);

  /// Clears the toast — called by [PosToast] after its exit animation.
  void clearToast() => state = state.copyWith(toast: null);

  // ── Flow resets ──────────────────────────────────────────────────────────

  /// Clears variant/add-on selections and quantity after adding an item to
  /// the cart.
  ///
  /// Category and product stay selected so the cashier can quickly add
  /// another unit of the same product with different options.
  void resetForNewItem() {
    state = state.copyWith(
        selectedVariantOptions: {},
        selectedAddons: {},
        selectedComponents: {},
        quantity: 1);
  }

  /// Full reset for "New Order" — clears all selections including category.
  void resetAll() => state = const PosState();
}

// ---------------------------------------------------------------------------
// DraftNotifier — in-memory parked orders for the session
// ---------------------------------------------------------------------------

/// Holds all parked (draft) orders created during the current session.
///
/// State is RAM-only, by design — parked orders are a same-shift convenience
/// ("hold this ticket while I ring up the next customer"), not a durable
/// record. Nothing here is written to disk, so the list is empty on every
/// app launch and a fresh, empty notifier is created whenever the signed-in
/// cashier changes (see [draftNotifierProvider], which is keyed off
/// [authNotifierProvider]) — one cashier never sees another's held tickets.
class DraftNotifier extends StateNotifier<List<DraftOrder>> {
  DraftNotifier() : super(const []);

  static const _uuid = Uuid();

  /// Parks the given [items] as a new draft with a display [ticketLabel].
  ///
  /// [taxRate] and [taxInclusive] are snapshotted at park time so the
  /// resumed cart uses the same tax configuration that was active.
  void park({
    required String ticketLabel,
    required List<CartItem> items,
    required Decimal taxRate,
    required bool taxInclusive,
  }) {
    final draft = DraftOrder(
      id: _uuid.v4(),
      label: ticketLabel,
      items: List.unmodifiable(items),
      taxRate: taxRate,
      taxInclusive: taxInclusive,
      createdAt: DateTime.now(),
    );
    // Prepend so the newest draft appears first in the list.
    state = [draft, ...state];
  }

  /// Removes the draft identified by [draftId].
  ///
  /// Called both when a cashier resumes a draft (load into cart → delete)
  /// and when they explicitly discard a parked order.
  void remove(String draftId) {
    state = state.where((d) => d.id != draftId).toList();
  }
}

// ---------------------------------------------------------------------------
// Providers
// ---------------------------------------------------------------------------

/// Global POS UI selection state.
///
/// keepAlive = true so category/product selections survive widget-tree rebuilds
/// (e.g. overlay animations).
final posNotifierProvider =
    StateNotifierProvider<PosNotifier, PosState>((ref) => PosNotifier());

/// In-memory draft orders for the current session.
///
/// Watching [authNotifierProvider] means a cashier switch (or logout) tears
/// down this notifier and creates a fresh, empty one for the new session —
/// see [DraftNotifier]'s doc comment for why that matters.
final draftNotifierProvider =
    StateNotifierProvider<DraftNotifier, List<DraftOrder>>((ref) {
  ref.watch(authNotifierProvider);
  return DraftNotifier();
});

/// Monotonically increasing ticket counter.
///
/// Starts at 1001 and increments with each "New Order" action.
/// Displayed in the POS header as the human-readable ticket reference.
final ticketCounterProvider = StateProvider<int>((ref) => 1001);
