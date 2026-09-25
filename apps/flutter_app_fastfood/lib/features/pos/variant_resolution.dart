// features/pos/variant_resolution.dart
//
// Shared, pure variant-resolution / pricing / cart-construction logic used by
// EVERY POS layout (grid_with_variant_picker's side panel, grid_quick_tap's
// instant-add + bottom sheet). This file exists specifically so that logic
// is never copy-pasted between layouts (spec Part F rule 3) — both layouts
// call these exact functions, never their own inline equivalents.
//
// Reactivity rule: none of these functions cache anything. Every one takes
// the current selections/data as parameters and recomputes from scratch, so
// callers that re-invoke them from a Riverpod `build()` on every state change
// (the correct pattern — see variant_panel.dart / quick_tap widgets) get a
// live, never-stale result. A price Text widget that reads a value computed
// once and never rebuilds is the exact bug this file exists to prevent.

import 'dart:convert';

import 'package:decimal/decimal.dart';
import 'package:uuid/uuid.dart';

import '../../db/app_database.dart';
import '../sale/cart_service.dart';
import '../sale/variant_inventory.dart';

/// Sorted, joined VariantOption ids — the same key scheme the backend uses
/// for `Variant.combination_key` (spec A1/D4). Pure, no I/O.
String combinationKey(Iterable<String> optionIds) {
  final sorted = optionIds.toList()..sort();
  return sorted.join(',');
}

/// Resolves the cashier's current Variant Option selections to a real,
/// synced [VariantsTableData] row — or `null` when no matching combination
/// exists.
///
/// Never synthesizes a Variant client-side (spec F4): every displayed price
/// comes from a resolved row here, not from `Product.basePrice`. A `null`
/// result means the caller must show "—" for price and block Add to Cart —
/// it must NEVER fall back to showing a stale or default price.
///
/// [selectedVariantOptions] is `groupId -> ONE optionId` (spec F1). A
/// zero-group product (no Variant Option Groups attached) always resolves to
/// its single default variant, matching spec D1 ("every product has ≥1
/// variant").
VariantsTableData? resolveSelectedVariant({
  required List<VariantOptionGroupsTableData> groups,
  required List<VariantsTableData> variants,
  required Map<String, String> selectedVariantOptions,
}) {
  if (groups.isEmpty) {
    if (variants.isEmpty) return null;
    return variants.firstWhere((v) => v.isDefault,
        orElse: () => variants.first);
  }
  if (selectedVariantOptions.length != groups.length) return null;
  final selected = <String>[];
  for (final g in groups) {
    final id = selectedVariantOptions[g.id];
    if (id == null) return null;
    selected.add(id);
  }
  final key = combinationKey(selected);
  for (final v in variants) {
    final ids = (jsonDecode(v.optionValueIds) as List).cast<String>();
    if (combinationKey(ids) == key) return v;
  }
  return null;
}

/// F3 — whether a product needs the customization picker/sheet at all, or
/// can be added to the cart instantly with its single default Variant.
///
/// Decided per-product, from that product's OWN variants/addonGroups/groups —
/// NEVER from its category or name. A drink with no Size option instant-adds;
/// a drink with a Size variant opens the picker, exactly like any other
/// variant product. There is deliberately no category-based branch here.
///
/// A product with an attached Inventory Component group (Laptop Store
/// shareable-inventory model — RAM, Storage, ...) always needs the picker
/// even when it has only its own single default Variant, since Component
/// Groups never generate extra combination Variants — without this check
/// the cashier could never reach the Components section to pick one.
bool productNeedsPicker({
  required List<VariantsTableData> variants,
  required List<AddonGroupsTableData> addonGroups,
  List<VariantOptionGroupsTableData> groups = const [],
}) {
  return variants.length > 1 ||
      addonGroups.isNotEmpty ||
      componentGroupsOf(groups).isNotEmpty;
}

/// Component Groups attached to a product (Laptop Store shareable-inventory
/// model) — never generate combination Variants; the cashier picks one
/// option per group at sale time, each resolving to its own independently
/// priced/stocked Variant via VariantOptionsTableData.componentVariantId.
List<VariantOptionGroupsTableData> componentGroupsOf(
        List<VariantOptionGroupsTableData> groups) =>
    groups.where((g) => g.usageType == 'inventory_component').toList();

/// The Variant Option Groups that still define this product's own
/// combination Variant (today's unchanged 'specification' behavior) —
/// the complement of [componentGroupsOf]. Passing the full [groups] list to
/// [resolveSelectedVariant]/[buildCartItem] would always fail resolution
/// for a product with any Component Group, since a component pick lives in
/// `selectedComponents`, never in `selectedVariantOptions`.
List<VariantOptionGroupsTableData> specificationGroupsOf(
        List<VariantOptionGroupsTableData> groups) =>
    groups.where((g) => g.usageType != 'inventory_component').toList();

/// Parses a Component Group's JSON-encoded allowed_option_ids — empty means
/// every option in the group is offered (spec §22 — compatibility is
/// product-specific).
List<String> allowedComponentOptionIds(VariantOptionGroupsTableData group) {
  if (group.allowedOptionIds.isEmpty) return const [];
  final decoded = jsonDecode(group.allowedOptionIds) as List;
  return decoded.cast<String>();
}

/// Whether every REQUIRED Component Group has a selection — the Components
/// analogue of `allGroupsSelected` for Variant Option Groups.
bool allRequiredComponentsSelected(
  List<VariantOptionGroupsTableData> componentGroups,
  Map<String, String> selectedComponents,
) =>
    componentGroups
        .where((g) => g.isRequired)
        .every((g) => selectedComponents.containsKey(g.id));

/// Sum of every currently-selected Add-on Item's price delta, across every
/// Add-on Group. Recomputed fresh from current selections on every call —
/// never cached — so a checkbox toggle is reflected the instant the caller
/// re-invokes this (spec: "Add-on totals must also be reactive").
Decimal resolveAddonsDelta({
  required List<AddonGroupsTableData> addonGroups,
  required Map<String, Set<String>> selectedAddons,
  required Map<String, List<AddonItemsTableData>> itemsByGroup,
}) {
  var total = Decimal.zero;
  for (final group in addonGroups) {
    final selectedIds = selectedAddons[group.id];
    if (selectedIds == null || selectedIds.isEmpty) continue;
    final items = itemsByGroup[group.id] ?? const [];
    for (final item in items) {
      if (selectedIds.contains(item.id)) {
        total += Decimal.tryParse(item.priceDelta) ?? Decimal.zero;
      }
    }
  }
  return total;
}

/// Sum of every currently-selected Inventory Component's own resolved
/// Variant price (Laptop Store shareable-inventory model) — priced
/// independently, like Add-ons, but each comes from a real, separately
/// stocked Variant rather than a delta. Recomputed fresh on every call,
/// same reactivity rule as [resolveAddonsDelta].
Decimal resolveComponentsDelta({
  required List<VariantOptionGroupsTableData> componentGroups,
  required Map<String, String> selectedComponents,
  required Map<String, VariantsTableData?> componentVariantByOptionId,
}) {
  var total = Decimal.zero;
  for (final group in componentGroups) {
    final optionId = selectedComponents[group.id];
    if (optionId == null) continue;
    final variant = componentVariantByOptionId[optionId];
    if (variant != null) {
      total += Decimal.tryParse(variant.salePrice) ?? Decimal.zero;
    }
  }
  return total;
}

/// Every reason an Add to Cart action can be blocked, kept distinct so the UI
/// can render a genuinely different visual state for each — not just a
/// disabled button with the same generic text (spec requirement).
enum AddToCartBlockReason {
  /// The cashier hasn't finished choosing one value per Variant Option Group
  /// (or the chosen combination has no matching synced Variant).
  incompleteSelection,

  /// A resolved, correctly-priced Variant that does not have enough stock.
  outOfStock,

  /// The combination is syntactically resolved locally but the server has
  /// marked it unsellable, or it hasn't synced yet.
  unavailable,
}

/// The result of evaluating whether the currently resolved variant/selection
/// can be added to the cart right now — the single "canSell()" gate shared by
/// every POS layout (spec requirement 6/point 3).
class AddToCartStatus {
  final AddToCartBlockReason? reason;
  final String message;

  const AddToCartStatus.ready()
      : reason = null,
        message = 'Ready to add';

  const AddToCartStatus.blocked(this.reason, this.message);

  bool get blocked => reason != null;
  bool get isOutOfStock => reason == AddToCartBlockReason.outOfStock;
  bool get isIncompleteSelection =>
      reason == AddToCartBlockReason.incompleteSelection;
}

/// Evaluates the full canSell() gate for the current selection: completeness,
/// then live stock via [VariantInventory]
/// — in that order, matching spec point 6 ("stock checking is part of
/// resolution, not an afterthought... call canSell() before enabling Add to
/// Cart").
///
/// This is the ONE function both POS layouts call to decide whether Add to
/// Cart is enabled — never re-implemented inline per layout.
Future<AddToCartStatus> evaluateAddToCartStatus({
  required VariantsTableData? resolvedVariant,
  required bool allGroupsSelected,
  required int quantity,
  required VariantInventory inventory,
  required CartSnapshot cart,
  // Laptop Store shareable-inventory model — the resolved Variant behind
  // each currently-selected Inventory Component, so its own stock is
  // checked exactly like the base Variant's, in the same canSell() gate
  // (null entries are skipped — an option not yet tracked as a component,
  // or one that failed to resolve, is reported separately as
  // incompleteSelection by the caller rather than silently ignored here).
  List<VariantsTableData?> selectedComponentVariants = const [],
}) async {
  if (!allGroupsSelected || resolvedVariant == null) {
    return const AddToCartStatus.blocked(
      AddToCartBlockReason.incompleteSelection,
      'Select an available option combination',
    );
  }
  final error =
      await inventory.selectionError(resolvedVariant.id, quantity, cart);
  if (error != null) {
    final reason = error.startsWith('Insufficient variant stock') ||
            error.contains('No in-stock units')
        ? AddToCartBlockReason.outOfStock
        : AddToCartBlockReason.unavailable;
    return AddToCartStatus.blocked(reason, error);
  }
  for (final componentVariant in selectedComponentVariants) {
    if (componentVariant == null) continue;
    final componentError =
        await inventory.selectionError(componentVariant.id, quantity, cart);
    if (componentError != null) {
      final reason = componentError.startsWith('Insufficient variant stock') ||
              componentError.contains('No in-stock units')
          ? AddToCartBlockReason.outOfStock
          : AddToCartBlockReason.unavailable;
      return AddToCartStatus.blocked(reason, componentError);
    }
  }
  return const AddToCartStatus.ready();
}

/// Builds a fully-resolved [CartItem] from the cashier's current selections —
/// the single construction path used by every POS layout and both the
/// side-panel and bottom-sheet customization UIs (spec Part F rule 3: never
/// duplicate cart-item construction per layout).
///
/// Resolves display-only [CartVariantOption]s from [selectedVariantOptions]
/// via [optionsByGroup], and priced [CartAddon]s — including synthesized
/// `wasRemoved: true` entries for unchecked `default_selected` items — from
/// [selectedAddons] via [addonItemsByGroup].
CartItem buildCartItem({
  required ProductsTableData product,
  required VariantsTableData variant,
  required List<VariantOptionGroupsTableData> groups,
  required Map<String, String> selectedVariantOptions,
  required Map<String, List<VariantOptionsTableData>> optionsByGroup,
  required List<AddonGroupsTableData> addonGroups,
  required Map<String, Set<String>> selectedAddons,
  required Map<String, List<AddonItemsTableData>> addonItemsByGroup,
  required int quantity,
  required String id,
}) {
  final variantOptions = <CartVariantOption>[];
  for (final group in groups) {
    final optionId = selectedVariantOptions[group.id];
    if (optionId == null) continue;
    final options = optionsByGroup[group.id] ?? const [];
    final option = options
        .cast<VariantOptionsTableData?>()
        .firstWhere((o) => o?.id == optionId, orElse: () => null);
    if (option != null) {
      variantOptions.add(
        CartVariantOption(
          variantOptionId: option.id,
          optionName: '${group.name}: ${option.name}',
        ),
      );
    }
  }

  final cartAddons = <CartAddon>[];
  for (final group in addonGroups) {
    final selectedIds = selectedAddons[group.id] ?? const {};
    final items = addonItemsByGroup[group.id] ?? const [];
    for (final item in items) {
      final isSelected = selectedIds.contains(item.id);
      if (isSelected) {
        cartAddons.add(CartAddon(
          addonItemId: item.id,
          addonName: item.name,
          priceDelta: Decimal.tryParse(item.priceDelta) ?? Decimal.zero,
          wasRemoved: false,
        ));
      } else if (item.defaultSelected) {
        cartAddons.add(CartAddon(
          addonItemId: item.id,
          addonName: item.name,
          priceDelta: Decimal.tryParse(item.priceDelta) ?? Decimal.zero,
          wasRemoved: true,
        ));
      }
    }
  }

  return CartItem(
    id: id,
    variantId: variant.id,
    productId: product.id,
    productName: product.name,
    unitPrice: Decimal.tryParse(variant.salePrice) ?? Decimal.zero,
    quantity: Decimal.fromInt(quantity),
    variantOptions: variantOptions,
    addons: cartAddons,
  );
}

/// Builds the base product's [CartItem] via [buildCartItem] PLUS one
/// ordinary sibling [CartItem] per currently-selected Inventory Component
/// (Laptop Store shareable-inventory model) — never a nested child, so
/// every other cart/pricing/stock code path treats a component exactly
/// like any other line. Each component is tagged back to the base item's
/// [id] via [CartItem.parentCartItemId]/[CartItem.satisfiesOptionGroupId]
/// so checkout can verify a required group was fulfilled and the receipt
/// can group it visually.
///
/// [componentOptionsById] and [componentVariantByOptionId] must already be
/// resolved by the caller (async DB reads) before calling this — this
/// function itself does no I/O, matching every other builder in this file.
List<CartItem> buildCartItems({
  required ProductsTableData product,
  required VariantsTableData variant,
  required List<VariantOptionGroupsTableData> groups,
  required Map<String, String> selectedVariantOptions,
  required Map<String, List<VariantOptionsTableData>> optionsByGroup,
  required List<AddonGroupsTableData> addonGroups,
  required Map<String, Set<String>> selectedAddons,
  required Map<String, List<AddonItemsTableData>> addonItemsByGroup,
  required List<VariantOptionGroupsTableData> componentGroups,
  required Map<String, String> selectedComponents,
  required Map<String, VariantOptionsTableData> componentOptionsById,
  required Map<String, VariantsTableData?> componentVariantByOptionId,
  required int quantity,
  required String id,
}) {
  final baseItem = buildCartItem(
    product: product,
    variant: variant,
    groups: groups,
    selectedVariantOptions: selectedVariantOptions,
    optionsByGroup: optionsByGroup,
    addonGroups: addonGroups,
    selectedAddons: selectedAddons,
    addonItemsByGroup: addonItemsByGroup,
    quantity: quantity,
    id: id,
  );

  final items = <CartItem>[baseItem];
  for (final group in componentGroups) {
    final optionId = selectedComponents[group.id];
    if (optionId == null) continue;
    final option = componentOptionsById[optionId];
    final componentVariant = componentVariantByOptionId[optionId];
    if (option == null || componentVariant == null) continue;
    final componentProductName = componentVariant.productName?.trim();
    final componentVariantName = componentVariant.variantName?.trim();
    final componentDisplayName =
        componentProductName == null || componentProductName.isEmpty
            ? '${group.name}: ${option.name}'
            : componentVariantName != null &&
                    componentVariantName.isNotEmpty &&
                    componentVariantName.toLowerCase() != 'default'
                ? '$componentProductName — $componentVariantName'
                : componentProductName;
    items.add(CartItem(
      // Sale item IDs are persisted and validated as UUIDs by the API. The
      // relationship to the configured product is represented separately by
      // parentCartItemId, so the line ID itself must never be a display key.
      id: const Uuid().v4(),
      variantId: componentVariant.id,
      productId: componentVariant.productId,
      productName: componentDisplayName,
      unitPrice: Decimal.tryParse(componentVariant.salePrice) ?? Decimal.zero,
      quantity: Decimal.fromInt(quantity),
      parentCartItemId: id,
      satisfiesOptionGroupId: group.id,
      componentOptionId: option.id,
    ));
  }
  return items;
}
