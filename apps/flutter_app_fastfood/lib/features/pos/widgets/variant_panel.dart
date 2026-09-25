// features/pos/widgets/variant_panel.dart
//
// Right-side panel — Steps 3 & 4 of the POS order flow.
//
// Empty state (no product selected):
//   Centered illustration prompting the cashier to pick a product.
//
// Product selected — two structurally separate sections (spec A1/D4/F4),
// each rendered only when the product actually has that kind of group
// attached:
//   • Variant Option Groups — single-select (radio), determines which real,
//     synced Variant (SKU) gets added. Never synthesized client-side — if the
//     chosen combination has no matching synced Variant, Add to Cart is
//     blocked with a prompt to sync/create it (spec F4).
//   • Add-on Groups — multi-select (checkbox), priced, never affects which
//     Variant is resolved.
//
// Field names from Drift schema:
//   ProductsTableData    → basePrice (TEXT) — seeded from PosSyncProduct.price
//   VariantsTableData    → salePrice (TEXT), optionValueIds (JSON TEXT)
//   AddonItemsTableData  → priceDelta (TEXT)

import 'package:decimal/decimal.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';

import '../../../db/app_database.dart';
import '../../../features/sale/variant_inventory.dart';
import '../../../providers/cart_notifier.dart';
import '../../../providers/currency_provider.dart';
import '../../../providers/database_provider.dart';
import '../../../providers/menu_provider.dart';
import '../pos_state.dart';
import '../pos_theme.dart';
import '../variant_resolution.dart';

/// Right-side variant/add-on panel.
///
/// Width is fixed by the parent [PosScreen] Row. All selections live in
/// [PosNotifier] — this widget only reads and renders them.
class VariantPanel extends ConsumerWidget {
  const VariantPanel({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedProductId = ref.watch(
      posNotifierProvider.select((s) => s.selectedProductId),
    );

    return selectedProductId == null
        ? const _EmptyState()
        : _ProductVariantView(productId: selectedProductId);
  }
}

// ── Empty state ──────────────────────────────────────────────────────────────

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.white,
      padding: const EdgeInsets.all(24),
      child: const Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.touch_app_outlined, size: 56, color: PosTheme.neutral200),
          SizedBox(height: 16),
          Text(
            'Pick a product',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w600,
              color: PosTheme.textMuted,
            ),
          ),
          SizedBox(height: 6),
          Text(
            'Tap any product to choose\noptions and add it to the cart',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 13, color: PosTheme.textMuted),
          ),
        ],
      ),
    );
  }
}

// ── Product variant view ─────────────────────────────────────────────────────

/// Loads Variant Option Groups, Add-on Groups, and synced Variants for
/// [productId], then renders the full panel once every data source is ready.
class _ProductVariantView extends ConsumerWidget {
  final String productId;
  const _ProductVariantView({required this.productId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final groupsAsync = ref.watch(variantOptionGroupsProvider(productId));
    final addonGroupsAsync = ref.watch(addonGroupsProvider(productId));
    final variantsAsync = ref.watch(variantsForProductProvider(productId));
    final allProductsAsync = ref.watch(allActiveProductsProvider);

    if (groupsAsync.isLoading ||
        addonGroupsAsync.isLoading ||
        variantsAsync.isLoading ||
        allProductsAsync.isLoading) {
      return const Center(
          child: CircularProgressIndicator(color: PosTheme.accent));
    }
    if (groupsAsync.hasError ||
        addonGroupsAsync.hasError ||
        variantsAsync.hasError ||
        allProductsAsync.hasError) {
      return const Center(
        child: Text(
          'Could not load this product',
          style: TextStyle(color: PosTheme.textMuted, fontSize: 12),
        ),
      );
    }

    final product = allProductsAsync.value!
        .cast<ProductsTableData?>()
        .firstWhere((p) => p?.id == productId, orElse: () => null);
    if (product == null) return const SizedBox.shrink();

    return VariantContent(
      product: product,
      groups: groupsAsync.value!,
      addonGroups: addonGroupsAsync.value!,
      variants: variantsAsync.value!,
    );
  }
}

// ── Variant content: variant groups + add-ons + stepper + add button ────────

class VariantContent extends ConsumerStatefulWidget {
  final ProductsTableData product;
  final List<VariantOptionGroupsTableData> groups;
  final List<AddonGroupsTableData> addonGroups;
  final List<VariantsTableData> variants;

  /// Called right after a successful add-to-cart. The side-panel layout
  /// leaves this null (it stays open so the cashier can add more units);
  /// the quick-tap layout's bottom sheet uses it to auto-dismiss.
  final VoidCallback? onAddedToCart;

  const VariantContent({
    super.key,
    required this.product,
    required this.groups,
    required this.addonGroups,
    required this.variants,
    this.onAddedToCart,
  });

  static const _uuid = Uuid();

  @override
  ConsumerState<VariantContent> createState() => _VariantContentState();
}

class _VariantContentState extends ConsumerState<VariantContent> {
  bool _adding = false;
  bool _addonsSeeded = false;

  ProductsTableData get product => widget.product;
  List<VariantOptionGroupsTableData> get groups => widget.groups;
  List<AddonGroupsTableData> get addonGroups => widget.addonGroups;
  List<VariantsTableData> get variants => widget.variants;

  @override
  void didUpdateWidget(covariant VariantContent oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.product.id != widget.product.id) {
      _addonsSeeded = false;
    }
  }

  void _seedDefaultAddons(PosState pos) {
    if (_addonsSeeded || addonGroups.isEmpty) return;
    final notifier = ref.read(posNotifierProvider.notifier);
    for (final group in addonGroups) {
      final itemsAsync = ref.read(addonItemsForGroupProvider(group.id));
      final items = itemsAsync.valueOrNull;
      if (items == null) return; // wait until every group's items are loaded
    }
    _addonsSeeded = true;
    for (final group in addonGroups) {
      final items = ref.read(addonItemsForGroupProvider(group.id)).value!;
      final defaults =
          items.where((i) => i.defaultSelected).map((i) => i.id).toSet();
      if (defaults.isNotEmpty) {
        notifier.seedDefaultAddons({group.id: defaults});
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final pos = ref.watch(posNotifierProvider);
    final posNotifier = ref.read(posNotifierProvider.notifier);

    WidgetsBinding.instance
        .addPostFrameCallback((_) => _seedDefaultAddons(pos));

    // Only 'specification'-usage groups ever define the combination Variant
    // — an 'inventory_component' group's pick lives in selectedComponents,
    // never selectedVariantOptions (see variant_resolution.dart).
    final specGroups = specificationGroupsOf(groups);
    final componentGroups = componentGroupsOf(groups);

    // Shared, pure resolution — the same function grid_quick_tap's instant-add
    // and bottom sheet call, so price/stock logic is never duplicated per
    // layout (spec Part F rule 3).
    final resolvedVariant = resolveSelectedVariant(
      groups: specGroups,
      variants: variants,
      selectedVariantOptions: pos.selectedVariantOptions,
    );
    final allGroupsSelected =
        specGroups.every((g) => pos.selectedVariantOptions.containsKey(g.id));
    final allComponentsSelected =
        allRequiredComponentsSelected(componentGroups, pos.selectedComponents);
    final selectionComplete = allGroupsSelected && allComponentsSelected;

    // Resolve each selected component's own Variant (Laptop Store
    // shareable-inventory model) for pricing/availability — reactive, so a
    // chip's price/stock updates the instant the underlying data syncs.
    final componentVariantByOptionId = <String, VariantsTableData?>{};
    for (final group in componentGroups) {
      final optionId = pos.selectedComponents[group.id];
      if (optionId == null) continue;
      final options =
          ref.watch(variantOptionsForGroupProvider(group.id)).valueOrNull ??
              const [];
      final option = options
          .cast<VariantOptionsTableData?>()
          .firstWhere((o) => o?.id == optionId, orElse: () => null);
      final componentVariantId = option?.componentVariantId;
      componentVariantByOptionId[optionId] = componentVariantId == null
          ? null
          : ref.watch(variantByIdProvider(componentVariantId)).valueOrNull;
    }

    // Never fall back to product.basePrice when nothing resolves — that was
    // the exact bug: showing a stale default-variant price while the cashier
    // is mid-selection. A null resolution means "—", not a guessed number.
    final basePrice = resolvedVariant != null
        ? Decimal.tryParse(resolvedVariant.salePrice) ?? Decimal.zero
        : null;

    final itemsByGroup = <String, List<AddonItemsTableData>>{
      for (final group in addonGroups)
        group.id: ref.watch(addonItemsForGroupProvider(group.id)).valueOrNull ??
            const [],
    };
    final addonsDelta = resolveAddonsDelta(
      addonGroups: addonGroups,
      selectedAddons: pos.selectedAddons,
      itemsByGroup: itemsByGroup,
    );
    final componentsDelta = resolveComponentsDelta(
      componentGroups: componentGroups,
      selectedComponents: pos.selectedComponents,
      componentVariantByOptionId: componentVariantByOptionId,
    );
    final unitPrice =
        basePrice == null ? null : basePrice + addonsDelta + componentsDelta;
    final lineTotal =
        unitPrice == null ? null : unitPrice * Decimal.fromInt(pos.quantity);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _PanelHeader(product: product, price: basePrice),
        Expanded(
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            children: [
              if (specGroups.isNotEmpty) ...[
                const _StepLabel('Step 3 — Variant'),
                const SizedBox(height: 4),
                for (var i = 0; i < specGroups.length; i++) ...[
                  if (i > 0) const Divider(height: 1, color: PosTheme.divider),
                  _VariantGroupSection(
                    group: specGroups[i],
                    selectedId: pos.selectedVariantOptions[specGroups[i].id],
                  ),
                ],
              ],
              if (componentGroups.isNotEmpty) ...[
                if (specGroups.isNotEmpty) const SizedBox(height: 8),
                const _StepLabel('Components'),
                const SizedBox(height: 4),
                for (var i = 0; i < componentGroups.length; i++) ...[
                  if (i > 0) const Divider(height: 1, color: PosTheme.divider),
                  _ComponentGroupSection(
                    group: componentGroups[i],
                    selectedId: pos.selectedComponents[componentGroups[i].id],
                  ),
                ],
              ],
              if (addonGroups.isNotEmpty) ...[
                if (specGroups.isNotEmpty || componentGroups.isNotEmpty)
                  const SizedBox(height: 8),
                const _StepLabel('Add-ons'),
                const SizedBox(height: 4),
                for (var i = 0; i < addonGroups.length; i++) ...[
                  if (i > 0) const Divider(height: 1, color: PosTheme.divider),
                  _AddonGroupSection(
                    group: addonGroups[i],
                    selectedIds:
                        pos.selectedAddons[addonGroups[i].id] ?? const {},
                  ),
                ],
              ],
              if (specGroups.isEmpty &&
                  componentGroups.isEmpty &&
                  addonGroups.isEmpty)
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 24),
                  child: Center(
                    child: Text(
                      'No options — ready to add',
                      style: TextStyle(color: PosTheme.textMuted, fontSize: 13),
                    ),
                  ),
                ),
            ],
          ),
        ),

        // Quantity stepper row.
        const Padding(
          padding: EdgeInsets.fromLTRB(16, 12, 16, 0),
          child: _StepLabel('Step 4 — Quantity'),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 6, 16, 0),
          child: _QuantityStepper(
            quantity: pos.quantity,
            onDecrement: posNotifier.decrementQty,
            onIncrement: posNotifier.incrementQty,
          ),
        ),

        Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
          child: _LineTotalBox(
            unitPrice: unitPrice,
            quantity: pos.quantity,
            lineTotal: lineTotal,
          ),
        ),

        Padding(
          padding: const EdgeInsets.fromLTRB(16, 10, 16, 20),
          child: FutureBuilder<AddToCartStatus>(
            future: _evaluateStatus(resolvedVariant, selectionComplete,
                pos.quantity, componentVariantByOptionId.values.toList()),
            builder: (context, snapshot) {
              final status = snapshot.data;
              final enabled =
                  snapshot.connectionState == ConnectionState.done &&
                      status != null &&
                      !status.blocked &&
                      !_adding;
              return Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  _StatusLine(status: status),
                  const SizedBox(height: 12),
                  _AddToCartButton(
                    enabled: enabled,
                    onTap: enabled
                        ? () => _addToCart(resolvedVariant!, pos)
                        : null,
                  ),
                ],
              );
            },
          ),
        ),
      ],
    );
  }

  /// The shared canSell() gate (spec point 6) — completeness, then live stock
  /// via [VariantInventory] for both the base
  /// Variant and every currently-selected Inventory Component. Never
  /// re-implemented inline; grid_quick_tap calls this exact function too.
  Future<AddToCartStatus> _evaluateStatus(
      VariantsTableData? variant,
      bool selectionComplete,
      int quantity,
      List<VariantsTableData?> selectedComponentVariants) {
    final db = ref.read(appDatabaseProvider);
    return evaluateAddToCartStatus(
      resolvedVariant: variant,
      allGroupsSelected: selectionComplete,
      quantity: quantity,
      inventory: VariantInventory(db),
      cart: ref.read(cartNotifierProvider),
      selectedComponentVariants: selectedComponentVariants,
    );
  }

  Future<void> _addToCart(VariantsTableData variant, PosState pos) async {
    if (_adding) return;
    setState(() => _adding = true);
    try {
      await _addToCartOnce(variant, pos);
    } catch (_) {
      ref
          .read(posNotifierProvider.notifier)
          .showToast('Could not add this item. Sync and try again.');
    } finally {
      if (mounted) setState(() => _adding = false);
    }
  }

//   Future<void> _addToCart(VariantsTableData variant, PosState pos) async {
//   if (_adding) return;

//   setState(() => _adding = true);

//   try {
//     await _addToCartOnce(variant, pos);
//   } catch (e, stackTrace) {
//     debugPrint('ADD TO CART ERROR: $e');
//     debugPrintStack(stackTrace: stackTrace);

//     ref
//         .read(posNotifierProvider.notifier)
//         .showToast('Could not add this item: $e');
//   } finally {
//     if (mounted) {
//       setState(() => _adding = false);
//     }
//   }
// }

  Future<void> _addToCartOnce(VariantsTableData variant, PosState pos) async {
    final cartNotifier = ref.read(cartNotifierProvider.notifier);
    final posNotifier = ref.read(posNotifierProvider.notifier);

    if (ref.read(posNotifierProvider).selectedProductId != product.id) return;

    final db = ref.read(appDatabaseProvider);
    final inventory = VariantInventory(db);
    final cart = ref.read(cartNotifierProvider);
    final error =
        await inventory.selectionError(variant.id, pos.quantity, cart);
    if (error != null) {
      posNotifier.showToast(error);
      return;
    }

    final specGroups = specificationGroupsOf(groups);
    final componentGroups = componentGroupsOf(groups);

    // Shared construction path (spec Part F rule 3) — resolves display-only
    // Variant Options and priced Add-ons (including removed defaults) and
    // builds the CartItem in one place used by every POS layout.
    final optionsByGroup = <String, List<VariantOptionsTableData>>{
      for (final group in specGroups)
        group.id:
            await ref.read(variantOptionsForGroupProvider(group.id).future),
    };
    final addonItemsByGroup = <String, List<AddonItemsTableData>>{
      for (final group in addonGroups)
        group.id: await ref.read(addonItemsForGroupProvider(group.id).future),
    };

    // Resolve every selected Inventory Component's own option row + Variant
    // (Laptop Store shareable-inventory model), and re-check ITS stock too
    // — the base Variant's availability alone is not enough to sell it.
    final componentOptionsById = <String, VariantOptionsTableData>{};
    final componentVariantByOptionId = <String, VariantsTableData?>{};
    for (final group in componentGroups) {
      final optionId = pos.selectedComponents[group.id];
      if (optionId == null) continue;
      final options =
          await ref.read(variantOptionsForGroupProvider(group.id).future);
      final option = options
          .cast<VariantOptionsTableData?>()
          .firstWhere((o) => o?.id == optionId, orElse: () => null);
      if (option == null) continue;
      componentOptionsById[optionId] = option;
      final componentVariantId = option.componentVariantId;
      if (componentVariantId == null) {
        posNotifier
            .showToast('"${option.name}" isn\'t set up as inventory yet.');
        return;
      }
      final componentVariant =
          await ref.read(variantByIdProvider(componentVariantId).future);
      componentVariantByOptionId[optionId] = componentVariant;
      if (componentVariant == null) continue;
      final componentError = await inventory.selectionError(
          componentVariant.id, pos.quantity, cart);
      if (componentError != null) {
        posNotifier.showToast(componentError);
        return;
      }
    }

    final configuredItems = buildCartItems(
      product: product,
      variant: variant,
      groups: specGroups,
      selectedVariantOptions: pos.selectedVariantOptions,
      optionsByGroup: optionsByGroup,
      addonGroups: addonGroups,
      selectedAddons: pos.selectedAddons,
      addonItemsByGroup: addonItemsByGroup,
      componentGroups: componentGroups,
      selectedComponents: pos.selectedComponents,
      componentOptionsById: componentOptionsById,
      componentVariantByOptionId: componentVariantByOptionId,
      quantity: pos.quantity,
      id: VariantContent._uuid.v4(),
    );
    cartNotifier.addItems(configuredItems);

    posNotifier.resetForNewItem();
    posNotifier.showToast('${product.name} added to cart');
    widget.onAddedToCart?.call();
  }
}

// ── Sub-widgets ──────────────────────────────────────────────────────────────

/// Header bar showing product name and current unit price.
///
/// [price] is null whenever no Variant has resolved for the current
/// selection — shown as "—", never a stale/guessed number.
class _PanelHeader extends ConsumerWidget {
  final ProductsTableData product;
  final Decimal? price;
  const _PanelHeader({required this.product, required this.price});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final money = ref.watch(moneyProvider);
    final p = price;
    final displayName =
        ref.watch(componentDisplayNameProvider(product.id)).valueOrNull ??
            product.name;
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 20, 16, 16),
      decoration: const BoxDecoration(
        color: PosTheme.accentLight,
        border: Border(
          bottom: BorderSide(color: PosTheme.divider, width: 1),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            displayName,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w700,
              color: PosTheme.accentText,
            ),
          ),
          if (product.description?.trim().isNotEmpty == true) ...[
            const SizedBox(height: 3),
            Text(
              product.description!.trim(),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                fontSize: 12,
                color: PosTheme.textMuted,
              ),
            ),
          ],
          const SizedBox(height: 4),
          Text(
            p == null ? '—' : money(p),
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w600,
              color: p == null ? PosTheme.textMuted : PosTheme.accent,
            ),
          ),
        ],
      ),
    );
  }
}

/// One Variant Option Group: radio-style single-select chip row.
class _VariantGroupSection extends ConsumerWidget {
  final VariantOptionGroupsTableData group;
  final String? selectedId;

  const _VariantGroupSection({required this.group, required this.selectedId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final optionsAsync = ref.watch(variantOptionsForGroupProvider(group.id));

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  group.name,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: PosTheme.text,
                  ),
                ),
              ),
              if (group.isRequired)
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: PosTheme.accentMid.withValues(alpha: 0.2),
                    borderRadius: PosTheme.pillRadius,
                  ),
                  child: const Text(
                    'Required',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                      color: PosTheme.accent,
                    ),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 10),
          optionsAsync.when(
            loading: () => const LinearProgressIndicator(
                minHeight: 2, color: PosTheme.accent),
            error: (e, _) => const Text(
              'Could not load options',
              style: TextStyle(color: PosTheme.textMuted, fontSize: 12),
            ),
            data: (options) => Wrap(
              spacing: 8,
              runSpacing: 8,
              children: options.map((opt) {
                final isSelected = selectedId == opt.id;
                return GestureDetector(
                  onTap: () => ref
                      .read(posNotifierProvider.notifier)
                      .selectVariantOption(group.id, opt.id),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 140),
                    padding:
                        const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                    decoration: BoxDecoration(
                      color: isSelected ? PosTheme.accent : PosTheme.surface,
                      borderRadius: PosTheme.pillRadius,
                      border: Border.all(
                        color: isSelected ? PosTheme.accent : PosTheme.divider,
                      ),
                    ),
                    child: Text(
                      opt.name,
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                        color: isSelected ? Colors.white : PosTheme.text,
                      ),
                    ),
                  ),
                );
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }
}

/// One Inventory Component Group (Laptop Store shareable-inventory model —
/// RAM, Storage, ...): radio-style single-select chip row, same interaction
/// as [_VariantGroupSection], but each chip resolves to its OWN
/// independently priced/stocked Variant instead of defining a combination
/// — selecting one never changes which Variant the base product itself
/// resolves to.
class _ComponentGroupSection extends ConsumerWidget {
  final VariantOptionGroupsTableData group;
  final String? selectedId;

  const _ComponentGroupSection({required this.group, required this.selectedId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final optionsAsync = ref.watch(variantOptionsForGroupProvider(group.id));
    final allowedIds = allowedComponentOptionIds(group);

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  group.name,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: PosTheme.text,
                  ),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: const Color(0xFF9333EA).withValues(alpha: 0.15),
                  borderRadius: PosTheme.pillRadius,
                ),
                child: const Text(
                  'Shared stock',
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF9333EA),
                  ),
                ),
              ),
              if (group.isRequired) ...[
                const SizedBox(width: 6),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: PosTheme.accentMid.withValues(alpha: 0.2),
                    borderRadius: PosTheme.pillRadius,
                  ),
                  child: const Text(
                    'Required',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                      color: PosTheme.accent,
                    ),
                  ),
                ),
              ],
            ],
          ),
          const SizedBox(height: 10),
          optionsAsync.when(
            loading: () => const LinearProgressIndicator(
                minHeight: 2, color: PosTheme.accent),
            error: (e, _) => const Text(
              'Could not load options',
              style: TextStyle(color: PosTheme.textMuted, fontSize: 12),
            ),
            data: (options) {
              // Empty allow-list means every option in the group is offered
              // (spec §22 — compatibility is product-specific).
              final visible = allowedIds.isEmpty
                  ? options
                  : options.where((o) => allowedIds.contains(o.id)).toList();
              if (visible.isEmpty) {
                return const Text(
                  'No values available for this product',
                  style: TextStyle(color: PosTheme.textMuted, fontSize: 12),
                );
              }
              return Wrap(
                spacing: 8,
                runSpacing: 8,
                children: visible
                    .map((opt) => _ComponentOptionChip(
                          groupId: group.id,
                          option: opt,
                          isSelected: selectedId == opt.id,
                        ))
                    .toList(),
              );
            },
          ),
        ],
      ),
    );
  }
}

/// One selectable Component chip — resolves its own price/stock via
/// [VariantOptionsTableData.componentVariantId] (a real, separately priced
/// and stocked Variant) and disables itself when that stock is unavailable,
/// exactly like a normal Variant option (spec §12 — inventory-aware POS
/// options). The authoritative gate is still [evaluateAddToCartStatus] at
/// Add-to-Cart time — this is only a fast, reactive UI hint.
class _ComponentOptionChip extends ConsumerWidget {
  final String groupId;
  final VariantOptionsTableData option;
  final bool isSelected;

  const _ComponentOptionChip({
    required this.groupId,
    required this.option,
    required this.isSelected,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final money = ref.watch(moneyProvider);
    final componentVariantId = option.componentVariantId;

    if (componentVariantId == null) {
      // Not yet tracked as an inventory item in the library — cannot be sold.
      return Opacity(
        opacity: 0.5,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
          decoration: BoxDecoration(
            color: PosTheme.surface,
            borderRadius: PosTheme.pillRadius,
            border: Border.all(color: PosTheme.divider),
          ),
          child: Text(
            '${option.name} (not stocked)',
            style: const TextStyle(fontSize: 12, color: PosTheme.textMuted),
          ),
        ),
      );
    }

    final variant =
        ref.watch(variantByIdProvider(componentVariantId)).valueOrNull;
    final stockRow = ref
        .watch(branchStockForVariantProvider(componentVariantId))
        .valueOrNull;
    final price = variant != null ? Decimal.tryParse(variant.salePrice) : null;
    // Untracked (no product/variant tracking) is always sellable, matching
    // VariantInventory.selectionError's own rule — only a real zero balance
    // on a quantity-tracked variant disables the chip here. Not-yet-loaded
    // (variant == null) fails open rather than flashing "unavailable"
    // during the first frame.
    final bool isAvailable;
    if (variant == null) {
      isAvailable = true;
    } else if (!variant.sellable) {
      isAvailable = false;
    } else if (!variant.allowInventoryTracking || !variant.tracksInventory) {
      isAvailable = true;
    } else {
      isAvailable = (stockRow?.quantity ?? 0) > 0;
    }

    return GestureDetector(
      onTap: !isAvailable
          ? null
          : () => ref
              .read(posNotifierProvider.notifier)
              .selectComponentOption(groupId, option.id),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 140),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: !isAvailable
              ? PosTheme.neutral200
              : (isSelected ? PosTheme.accent : PosTheme.surface),
          borderRadius: PosTheme.pillRadius,
          border: Border.all(
            color: isSelected ? PosTheme.accent : PosTheme.divider,
          ),
        ),
        child: Text(
          price == null ? option.name : '${option.name}  ${money(price)}',
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w500,
            color: !isAvailable
                ? PosTheme.textMuted
                : (isSelected ? Colors.white : PosTheme.text),
            decoration: !isAvailable ? TextDecoration.lineThrough : null,
          ),
        ),
      ),
    );
  }
}

/// One Add-on Group: checkbox-style multi-select chip row, priced.
class _AddonGroupSection extends ConsumerWidget {
  final AddonGroupsTableData group;
  final Set<String> selectedIds;

  const _AddonGroupSection({required this.group, required this.selectedIds});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final itemsAsync = ref.watch(addonItemsForGroupProvider(group.id));
    final money = ref.watch(moneyProvider);

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  group.maxSelect != null
                      ? '${group.name}  (pick up to ${group.maxSelect})'
                      : group.name,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: PosTheme.text,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          itemsAsync.when(
            loading: () => const LinearProgressIndicator(
                minHeight: 2, color: PosTheme.accent),
            error: (e, _) => const Text(
              'Could not load add-ons',
              style: TextStyle(color: PosTheme.textMuted, fontSize: 12),
            ),
            data: (items) => Wrap(
              spacing: 8,
              runSpacing: 8,
              children: items.map((item) {
                final isSelected = selectedIds.contains(item.id);
                final priceDelta =
                    Decimal.tryParse(item.priceDelta) ?? Decimal.zero;
                final hasExtra = priceDelta > Decimal.zero;
                return GestureDetector(
                  onTap: () => ref
                      .read(posNotifierProvider.notifier)
                      .toggleAddon(group.id, item.id,
                          maxSelections: group.maxSelect),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 140),
                    padding:
                        const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                    decoration: BoxDecoration(
                      color: isSelected ? PosTheme.accent : PosTheme.surface,
                      borderRadius: PosTheme.pillRadius,
                      border: Border.all(
                        color: isSelected ? PosTheme.accent : PosTheme.divider,
                      ),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          isSelected
                              ? Icons.check_box
                              : Icons.check_box_outline_blank,
                          size: 14,
                          color: isSelected ? Colors.white : PosTheme.textMuted,
                        ),
                        const SizedBox(width: 6),
                        Text(
                          hasExtra
                              ? '${item.name}  +${money(priceDelta)}'
                              : item.name,
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w500,
                            color: isSelected ? Colors.white : PosTheme.text,
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }
}

class _QuantityStepper extends StatelessWidget {
  final int quantity;
  final VoidCallback onDecrement;
  final VoidCallback onIncrement;

  const _QuantityStepper({
    required this.quantity,
    required this.onDecrement,
    required this.onIncrement,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        const Text(
          'Quantity',
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w600,
            color: PosTheme.text,
          ),
        ),
        Container(
          decoration: BoxDecoration(
            color: PosTheme.surface,
            borderRadius: PosTheme.pillRadius,
            border: Border.all(color: PosTheme.divider),
          ),
          child: Row(
            children: [
              GestureDetector(
                onTap: onDecrement,
                child: const SizedBox(
                  width: 36,
                  height: 36,
                  child: Icon(Icons.remove, size: 18, color: PosTheme.text),
                ),
              ),
              SizedBox(
                width: 40,
                child: Text(
                  '$quantity',
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                    color: PosTheme.text,
                  ),
                ),
              ),
              GestureDetector(
                onTap: onIncrement,
                child: const SizedBox(
                  width: 36,
                  height: 36,
                  child: Icon(Icons.add, size: 18, color: PosTheme.accent),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

/// Small uppercase "Step N — …" eyebrow label (matches the design mock).
class _StepLabel extends StatelessWidget {
  final String text;
  const _StepLabel(this.text);

  @override
  Widget build(BuildContext context) {
    return Text(
      text.toUpperCase(),
      style: const TextStyle(
        fontSize: 11,
        fontWeight: FontWeight.w700,
        letterSpacing: 1.4,
        color: PosTheme.accentText,
      ),
    );
  }
}

/// Green summary box: unit price × qty on the left, big line total on the right.
/// [unitPrice]/[lineTotal] are null whenever no Variant has resolved for the
/// current selection — shown as "—", never a stale/guessed price.
class _LineTotalBox extends ConsumerWidget {
  final Decimal? unitPrice;
  final int quantity;
  final Decimal? lineTotal;

  const _LineTotalBox({
    required this.unitPrice,
    required this.quantity,
    required this.lineTotal,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final money = ref.watch(moneyProvider);
    final unit = unitPrice;
    final total = lineTotal;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: PosTheme.accent2Light,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        children: [
          Text(
            unit == null
                ? '— each × $quantity'
                : '${money(unit)} each × $quantity',
            style: const TextStyle(fontSize: 12, color: PosTheme.accent2Text),
          ),
          const Spacer(),
          Text(
            total == null ? '—' : money(total),
            style: const TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w800,
              color: PosTheme.accent2Text,
            ),
          ),
        ],
      ),
    );
  }
}

/// Renders the current [AddToCartStatus] with a visual treatment that is
/// genuinely distinct per block reason — "out of stock" and "incomplete
/// selection" never share the same icon/color, only a disabled button with
/// different text is not enough (spec requirement).
class _StatusLine extends StatelessWidget {
  final AddToCartStatus? status;
  const _StatusLine({required this.status});

  @override
  Widget build(BuildContext context) {
    final s = status;
    if (s == null) {
      return const Text('Checking availability…',
          style: TextStyle(color: PosTheme.textMuted));
    }
    if (!s.blocked) {
      return const Row(
        children: [
          Icon(Icons.check_circle, size: 16, color: PosTheme.accent),
          SizedBox(width: 6),
          Text('Ready to add', style: TextStyle(color: PosTheme.textMuted)),
        ],
      );
    }
    final IconData icon;
    final Color color;
    switch (s.reason) {
      case AddToCartBlockReason.outOfStock:
        icon = Icons.block;
        color = const Color(0xFFDC2626); // red — genuinely out of stock
        break;
      case AddToCartBlockReason.unavailable:
        icon = Icons.sync_problem;
        color = const Color(0xFF9333EA); // purple — a sync/data issue
        break;
      case AddToCartBlockReason.incompleteSelection:
      case null:
        icon = Icons.touch_app_outlined;
        color = const Color(0xFFC2410C); // amber — just finish choosing
        break;
    }
    return Row(
      children: [
        Icon(icon, size: 16, color: color),
        const SizedBox(width: 6),
        Expanded(
          child: Text(s.message, style: TextStyle(color: color)),
        ),
      ],
    );
  }
}

class _AddToCartButton extends StatelessWidget {
  final bool enabled;
  final VoidCallback? onTap;

  const _AddToCartButton({required this.enabled, this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        height: 52,
        decoration: BoxDecoration(
          color: enabled ? PosTheme.accent : PosTheme.neutral200,
          borderRadius: PosTheme.pillRadius,
          boxShadow: enabled ? PosTheme.shadowMd : const [],
        ),
        alignment: Alignment.center,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.add_shopping_cart,
              size: 20,
              color: enabled ? Colors.white : PosTheme.textMuted,
            ),
            const SizedBox(width: 8),
            Text(
              'Add to Cart',
              style: TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.w700,
                color: enabled ? Colors.white : PosTheme.textMuted,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
