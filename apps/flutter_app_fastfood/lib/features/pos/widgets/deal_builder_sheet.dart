// features/pos/widgets/deal_builder_sheet.dart
//
// Combo-builder sheet opened when a cashier taps a Deal tile in the POS
// grid (see category_rail.dart's "Deals" pseudo-category and
// product_grid.dart's deal-grid branch).
//
// Each DealItem slot resolves to a product two ways:
//   • product_id set  → locked, no swap control.
//   • category_id set → cashier picks exactly one product from that category.
// Either way, once the product is known its own Add-on Groups render for
// normal selection (flavor, extra cheese, etc.) — the deal only locks which
// PRODUCT is in each slot, never its add-ons.
//
// "Add to Order" resolves every slot into an ordinary CartItem via the same
// buildCartItem() every other POS layout uses (variant_resolution.dart) —
// no new cart-linkage concept needed, these are independent lines like any
// other product. The cart is tagged with this deal via CartNotifier.setDeal
// (the same field the existing "Offers and deals" flow already threads to
// the API, see cart_overlay.dart). When the deal has a fixed_price, the
// cart-level discount is set so the slots' natural total matches it exactly.
//
// Known simplification: a category slot includes any product in that
// category at the same flat rate (free when DealItem.is_free, otherwise
// full price) — there's no per-product upcharge field on DealItem, so
// (unlike a generic POS combo-builder) swapping to a pricier item in the
// category never adds a difference.

import 'package:decimal/decimal.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';

import '../../../db/app_database.dart';
import '../../../providers/cart_notifier.dart';
import '../../../providers/currency_provider.dart';
import '../../../providers/menu_provider.dart';
import '../../sale/cart_service.dart';
import '../pos_state.dart';
import '../pos_theme.dart';
import '../variant_resolution.dart';

const _uuid = Uuid();

/// Opens the combo-builder sheet for [deal]. Mirrors quick_tap_grid.dart's
/// `_CustomizationSheet` chrome (isScrollControlled, rounded-top sheet,
/// drag-handle bar) so a deal and a regular product picker feel identical.
Future<void> showDealBuilderSheet(BuildContext context, DealsTableData deal) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.white,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
    ),
    builder: (_) => _DealBuilderSheet(deal: deal),
  );
}

class _SlotSelection {
  String? productId;
  final Map<String, Set<String>> selectedAddons = {};
}

class _DealBuilderSheet extends ConsumerStatefulWidget {
  final DealsTableData deal;
  const _DealBuilderSheet({required this.deal});

  @override
  ConsumerState<_DealBuilderSheet> createState() => _DealBuilderSheetState();
}

class _DealBuilderSheetState extends ConsumerState<_DealBuilderSheet> {
  final Map<int, _SlotSelection> _slots = {};
  bool _adding = false;

  _SlotSelection _slotFor(int index) =>
      _slots.putIfAbsent(index, () => _SlotSelection());

  bool _allSlotsResolved(List<DealItemsTableData> items) {
    for (var i = 0; i < items.length; i++) {
      final item = items[i];
      if (item.productId == null && _slotFor(i).productId == null) {
        return false;
      }
    }
    return true;
  }

  @override
  Widget build(BuildContext context) {
    final itemsAsync = ref.watch(dealItemsForDealProvider(widget.deal.id));

    return SafeArea(
      child: FractionallySizedBox(
        heightFactor: 0.88,
        child: Column(
          children: [
            const Padding(
              padding: EdgeInsets.only(top: 10, bottom: 4),
              child: _DragHandle(),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 4, 16, 8),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      widget.deal.name,
                      style: const TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.w700,
                        color: PosTheme.text,
                      ),
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, color: PosTheme.textMuted),
                    onPressed: () => Navigator.of(context).pop(),
                  ),
                ],
              ),
            ),
            const Divider(height: 1, color: PosTheme.divider),
            Expanded(
              child: itemsAsync.when(
                loading: () => const Center(
                  child: CircularProgressIndicator(color: PosTheme.accent),
                ),
                error: (_, __) => const Center(
                  child: Text(
                    'Could not load this deal',
                    style: TextStyle(color: PosTheme.textMuted),
                  ),
                ),
                data: (items) => items.isEmpty
                    ? const Center(
                        child: Text(
                          'This deal has no items configured',
                          style: TextStyle(color: PosTheme.textMuted),
                        ),
                      )
                    : ListView.separated(
                        padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
                        itemCount: items.length,
                        separatorBuilder: (_, __) => const SizedBox(height: 16),
                        itemBuilder: (context, i) => _DealItemSlot(
                          item: items[i],
                          selection: _slotFor(i),
                          onChanged: () => setState(() {}),
                        ),
                      ),
              ),
            ),
            itemsAsync.maybeWhen(
              data: (items) => _DealFooter(
                deal: widget.deal,
                items: items,
                adding: _adding,
                enabled: items.isNotEmpty && _allSlotsResolved(items),
                onAddToOrder: () => _addToOrder(items),
              ),
              orElse: () => const SizedBox.shrink(),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _addToOrder(List<DealItemsTableData> items) async {
    if (_adding || !_allSlotsResolved(items)) return;
    setState(() => _adding = true);
    try {
      final allProducts = await ref.read(allActiveProductsProvider.future);
      final cartItems = <CartItem>[];

      for (var i = 0; i < items.length; i++) {
        final dealItem = items[i];
        final productId = dealItem.productId ?? _slotFor(i).productId!;
        final product = allProducts
            .cast<ProductsTableData?>()
            .firstWhere((p) => p?.id == productId, orElse: () => null);
        if (product == null) continue;

        final variants =
            await ref.read(variantsForProductProvider(productId).future);
        if (variants.isEmpty) continue;
        final variant = variants
                .cast<VariantsTableData?>()
                .firstWhere((v) => v?.isDefault == true, orElse: () => null) ??
            variants.first;

        final addonGroups =
            await ref.read(addonGroupsProvider(productId).future);
        final addonItemsByGroup = <String, List<AddonItemsTableData>>{};
        for (final group in addonGroups) {
          addonItemsByGroup[group.id] =
              await ref.read(addonItemsForGroupProvider(group.id).future);
        }

        var cartItem = buildCartItem(
          product: product,
          variant: variant,
          groups: const [],
          selectedVariantOptions: const {},
          optionsByGroup: const {},
          addonGroups: addonGroups,
          selectedAddons: _slotFor(i).selectedAddons,
          addonItemsByGroup: addonItemsByGroup,
          quantity: dealItem.quantity,
          id: _uuid.v4(),
        );

        if (dealItem.isFree) {
          final rawTotal =
              (cartItem.unitPrice + cartItem.addonsTotal) * cartItem.quantity;
          cartItem = cartItem.copyWith(discount: rawTotal);
        }

        cartItems.add(cartItem);
      }

      if (cartItems.isEmpty) {
        if (mounted) {
          ref
              .read(posNotifierProvider.notifier)
              .showToast('Could not add this deal — no items resolved.');
        }
        return;
      }

      final cartNotifier = ref.read(cartNotifierProvider.notifier);
      cartNotifier.addItems(cartItems);
      // A cart reflects exactly one Promotion/Deal source at a time — same
      // invariant cart_overlay.dart's _applyDiscount keeps (see its comment).
      cartNotifier.setPromotion(null);
      cartNotifier.setDeal(widget.deal.id);

      final fixedPrice = widget.deal.fixedPrice == null
          ? null
          : Decimal.tryParse(widget.deal.fixedPrice!);
      if (fixedPrice != null) {
        final naturalTotal = cartItems.fold(
          Decimal.zero,
          (sum, item) => sum + item.lineTotal,
        );
        final adjustment = naturalTotal - fixedPrice;
        if (adjustment > Decimal.zero) {
          cartNotifier.setDiscount(adjustment);
        }
      }

      if (mounted) {
        Navigator.of(context).pop();
        ref
            .read(posNotifierProvider.notifier)
            .showToast('${widget.deal.name} added to cart');
      }
    } finally {
      if (mounted) setState(() => _adding = false);
    }
  }
}

class _DragHandle extends StatelessWidget {
  const _DragHandle();
  @override
  Widget build(BuildContext context) {
    return Container(
      width: 40,
      height: 4,
      decoration: BoxDecoration(
        color: PosTheme.divider,
        borderRadius: BorderRadius.circular(2),
      ),
    );
  }
}

// ── One deal-item slot: locked product, or a category pick, + its addons ──

class _DealItemSlot extends ConsumerWidget {
  final DealItemsTableData item;
  final _SlotSelection selection;
  final VoidCallback onChanged;

  const _DealItemSlot({
    required this.item,
    required this.selection,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (item.productId != null) {
      return _LockedProductSlot(
        productId: item.productId!,
        isFree: item.isFree,
        selection: selection,
        onChanged: onChanged,
      );
    }
    return _CategorySlot(
      categoryId: item.categoryId!,
      isFree: item.isFree,
      selection: selection,
      onChanged: onChanged,
    );
  }
}

class _LockedProductSlot extends ConsumerWidget {
  final String productId;
  final bool isFree;
  final _SlotSelection selection;
  final VoidCallback onChanged;

  const _LockedProductSlot({
    required this.productId,
    required this.isFree,
    required this.selection,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final productsAsync = ref.watch(allActiveProductsProvider);
    final product = productsAsync.valueOrNull
        ?.cast<ProductsTableData?>()
        .firstWhere((p) => p?.id == productId, orElse: () => null);

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: PosTheme.surface,
        borderRadius: PosTheme.tileRadius,
        border: Border.all(color: PosTheme.divider),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.lock_outline,
                  size: 16, color: PosTheme.textMuted),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  product?.name ?? 'Loading…',
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: PosTheme.text,
                  ),
                ),
              ),
              if (isFree) const _FreeBadge(),
            ],
          ),
          if (product != null)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: _AddonGroups(
                productId: product.id,
                selection: selection,
                onChanged: onChanged,
              ),
            ),
        ],
      ),
    );
  }
}

class _CategorySlot extends ConsumerWidget {
  final String categoryId;
  final bool isFree;
  final _SlotSelection selection;
  final VoidCallback onChanged;

  const _CategorySlot({
    required this.categoryId,
    required this.isFree,
    required this.selection,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final categoriesAsync = ref.watch(categoriesProvider);
    final category = categoriesAsync.valueOrNull
        ?.cast<CategoriesTableData?>()
        .firstWhere((c) => c?.id == categoryId, orElse: () => null);
    final productsAsync = ref.watch(productsByCategoryProvider(categoryId));

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: PosTheme.surface,
        borderRadius: PosTheme.tileRadius,
        border: Border.all(color: PosTheme.divider),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  'Choose one · ${category?.name ?? '…'}',
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: PosTheme.text,
                  ),
                ),
              ),
              if (isFree) const _FreeBadge(),
            ],
          ),
          const SizedBox(height: 8),
          productsAsync.when(
            loading: () => const Padding(
              padding: EdgeInsets.symmetric(vertical: 8),
              child: SizedBox(
                height: 20,
                width: 20,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
            ),
            error: (_, __) => const Text(
              'Could not load products',
              style: TextStyle(color: PosTheme.textMuted, fontSize: 12),
            ),
            data: (products) => Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (final product in products)
                  _ChoiceChip(
                    label: product.name,
                    selected: selection.productId == product.id,
                    onTap: () {
                      selection.productId = product.id;
                      selection.selectedAddons.clear();
                      onChanged();
                    },
                  ),
              ],
            ),
          ),
          if (selection.productId != null)
            Padding(
              padding: const EdgeInsets.only(top: 10),
              child: _AddonGroups(
                productId: selection.productId!,
                selection: selection,
                onChanged: onChanged,
              ),
            ),
        ],
      ),
    );
  }
}

class _FreeBadge extends StatelessWidget {
  const _FreeBadge();
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: const BoxDecoration(
        color: PosTheme.accent2Light,
        borderRadius: PosTheme.pillRadius,
      ),
      child: const Text(
        'Included',
        style: TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.w700,
          color: PosTheme.accent2Text,
        ),
      ),
    );
  }
}

class _ChoiceChip extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;

  const _ChoiceChip({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: selected ? PosTheme.accent : Colors.white,
          borderRadius: PosTheme.pillRadius,
          border: Border.all(
            color: selected ? PosTheme.accent : PosTheme.divider,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w600,
            color: selected ? Colors.white : PosTheme.text,
          ),
        ),
      ),
    );
  }
}

// ── Add-on groups for whichever product is currently resolved in a slot ──

class _AddonGroups extends ConsumerWidget {
  final String productId;
  final _SlotSelection selection;
  final VoidCallback onChanged;

  const _AddonGroups({
    required this.productId,
    required this.selection,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final groupsAsync = ref.watch(addonGroupsProvider(productId));
    return groupsAsync.when(
      loading: () => const SizedBox.shrink(),
      error: (_, __) => const SizedBox.shrink(),
      data: (groups) {
        if (groups.isEmpty) return const SizedBox.shrink();
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            for (final group in groups)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: _AddonGroupRow(
                  group: group,
                  selection: selection,
                  onChanged: onChanged,
                ),
              ),
          ],
        );
      },
    );
  }
}

class _AddonGroupRow extends ConsumerWidget {
  final AddonGroupsTableData group;
  final _SlotSelection selection;
  final VoidCallback onChanged;

  const _AddonGroupRow({
    required this.group,
    required this.selection,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final itemsAsync = ref.watch(addonItemsForGroupProvider(group.id));
    final money = ref.watch(moneyProvider);
    final singleSelect = group.maxSelect == 1;

    return itemsAsync.when(
      loading: () => const SizedBox.shrink(),
      error: (_, __) => const SizedBox.shrink(),
      data: (items) {
        if (items.isEmpty) return const SizedBox.shrink();
        final selectedIds = selection.selectedAddons[group.id] ?? const {};
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              group.name,
              style: const TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w700,
                color: PosTheme.textMuted,
              ),
            ),
            const SizedBox(height: 4),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: [
                for (final addonItem in items)
                  _ChoiceChip(
                    label: Decimal.tryParse(addonItem.priceDelta) ==
                            Decimal.zero
                        ? addonItem.name
                        : '${addonItem.name} +${money(Decimal.tryParse(addonItem.priceDelta) ?? Decimal.zero)}',
                    selected: selectedIds.contains(addonItem.id),
                    onTap: () {
                      final current = Set<String>.from(selectedIds);
                      if (singleSelect) {
                        current
                          ..clear()
                          ..add(addonItem.id);
                      } else if (current.contains(addonItem.id)) {
                        current.remove(addonItem.id);
                      } else {
                        current.add(addonItem.id);
                      }
                      selection.selectedAddons[group.id] = current;
                      onChanged();
                    },
                  ),
              ],
            ),
          ],
        );
      },
    );
  }
}

// ── Footer: running total + Add to Order ──

class _DealFooter extends ConsumerWidget {
  final DealsTableData deal;
  final List<DealItemsTableData> items;
  final bool adding;
  final bool enabled;
  final VoidCallback onAddToOrder;

  const _DealFooter({
    required this.deal,
    required this.items,
    required this.adding,
    required this.enabled,
    required this.onAddToOrder,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final money = ref.watch(moneyProvider);
    final fixedPrice =
        deal.fixedPrice == null ? null : Decimal.tryParse(deal.fixedPrice!);

    return Container(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
      decoration: const BoxDecoration(
        color: PosTheme.accent2Light,
        border: Border(top: BorderSide(color: PosTheme.divider)),
      ),
      child: Row(
        children: [
          if (fixedPrice != null)
            Expanded(
              child: Text(
                'Deal price: ${money(fixedPrice)}',
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                  color: PosTheme.accent2Text,
                ),
              ),
            )
          else
            const Expanded(
              child: Text(
                'Select an item for every slot',
                style: TextStyle(fontSize: 12, color: PosTheme.textMuted),
              ),
            ),
          SizedBox(
            width: 160,
            child: ElevatedButton(
              onPressed: enabled && !adding ? onAddToOrder : null,
              style: ElevatedButton.styleFrom(
                backgroundColor: PosTheme.accent,
                disabledBackgroundColor: PosTheme.divider,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 12),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: adding
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : const Text(
                      'Add to Order',
                      style: TextStyle(fontWeight: FontWeight.w700),
                    ),
            ),
          ),
        ],
      ),
    );
  }
}
