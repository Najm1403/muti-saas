// features/pos/widgets/quick_tap_grid.dart
//
// grid_quick_tap layout (spec Part C / G4) — large tap tiles for high-volume
// counter selling (e.g. fast food). Tapping a product either adds it
// instantly (that specific product has no variants beyond its single
// default, and no Add-on Groups) or opens a lightweight bottom sheet for
// products that need customization.
//
// The instant-add-vs-sheet decision is made per product, from THAT product's
// own variants/addonGroups (via [productNeedsPicker]) — never from its
// category or name. A drink with no Size option instant-adds; a drink with a
// Size variant opens the sheet, exactly like any other variant product.
//
// Shares every piece of resolution/pricing/stock-check/cart-construction
// logic with the grid_with_variant_picker layout via variant_resolution.dart,
// and reuses the exact same [VariantContent] widget (variant_panel.dart) for
// the sheet — nothing here re-implements that logic or that UI.

import 'package:decimal/decimal.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';

import '../../../core/network/dio_client.dart' show assetUrl;
import '../../../db/app_database.dart';
import '../../../features/sale/variant_inventory.dart';
import '../../../providers/cart_notifier.dart';
import '../../../providers/currency_provider.dart';
import '../../../providers/database_provider.dart';
import '../../../providers/menu_provider.dart';
import '../pos_state.dart';
import '../pos_theme.dart';
import '../variant_resolution.dart';
import 'variant_panel.dart';

/// Large-tile product grid for the currently selected category.
class QuickTapGrid extends ConsumerWidget {
  const QuickTapGrid({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedCategoryId = ref.watch(
      posNotifierProvider.select((s) => s.selectedCategoryId),
    );
    final searchQuery =
        ref.watch(posNotifierProvider.select((s) => s.searchQuery)).trim();
    final isSearching = searchQuery.isNotEmpty;

    if (!isSearching && selectedCategoryId == null) {
      return const _EmptyPrompt(
        icon: Icons.category_outlined,
        message: 'Select a category to browse products',
      );
    }

    final productsAsync = isSearching
        ? ref.watch(searchProductsProvider(searchQuery))
        : ref.watch(productsByCategoryProvider(selectedCategoryId!));
    final cartSnapshot = ref.watch(cartNotifierProvider);

    final cartQtyMap = <String, int>{};
    for (final item in cartSnapshot.items) {
      cartQtyMap[item.productId] =
          (cartQtyMap[item.productId] ?? 0) + item.quantity.toBigInt().toInt();
    }

    return productsAsync.when(
      loading: () => const _LoadingGrid(),
      error: (e, _) => const _EmptyPrompt(
        icon: Icons.error_outline,
        message: 'Could not load products',
      ),
      data: (products) {
        if (products.isEmpty) {
          return _EmptyPrompt(
            icon: isSearching ? Icons.search_off : Icons.no_food,
            message: isSearching
                ? 'No products match "$searchQuery"'
                : 'No products in this category',
          );
        }
        return GridView.builder(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
          gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
            maxCrossAxisExtent: 170,
            crossAxisSpacing: 14,
            mainAxisSpacing: 14,
            childAspectRatio: 0.95,
          ),
          itemCount: products.length,
          itemBuilder: (context, index) => _QuickTapTile(
            product: products[index],
            qtyInCart: cartQtyMap[products[index].id] ?? 0,
          ),
        );
      },
    );
  }
}

// ── One tap tile ─────────────────────────────────────────────────────────────

class _QuickTapTile extends ConsumerStatefulWidget {
  final ProductsTableData product;
  final int qtyInCart;

  const _QuickTapTile({required this.product, required this.qtyInCart});

  @override
  ConsumerState<_QuickTapTile> createState() => _QuickTapTileState();
}

class _QuickTapTileState extends ConsumerState<_QuickTapTile> {
  static const _uuid = Uuid();
  bool _busy = false;

  Future<void> _handleTap() async {
    if (_busy) return;
    setState(() => _busy = true);
    try {
      final groups =
          await ref.read(variantOptionGroupsProvider(widget.product.id).future);
      final addonGroups =
          await ref.read(addonGroupsProvider(widget.product.id).future);
      final variants =
          await ref.read(variantsForProductProvider(widget.product.id).future);
      if (!mounted) return;

      // F3 — decided per-product, from THIS product's own data. No category
      // or name check anywhere in this file. A product with an attached
      // Inventory Component group always needs the picker too (Laptop
      // Store shareable-inventory model) — see productNeedsPicker's doc.
      final needsPicker = productNeedsPicker(
          variants: variants, addonGroups: addonGroups, groups: groups);

      if (needsPicker) {
        await _openSheet(groups, addonGroups, variants);
        return;
      }

      await _addInstantly(groups, addonGroups, variants);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _openSheet(
    List<VariantOptionGroupsTableData> groups,
    List<AddonGroupsTableData> addonGroups,
    List<VariantsTableData> variants,
  ) async {
    // Same global selection state the side-panel layout uses — selecting the
    // product resets variant/add-on/quantity to a clean slate for it.
    ref.read(posNotifierProvider.notifier).selectProduct(widget.product.id);
    if (!mounted) return;
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (sheetContext) => _CustomizationSheet(
        product: widget.product,
        groups: groups,
        addonGroups: addonGroups,
        variants: variants,
      ),
    );
  }

  /// A zero-option, no-add-on product — resolve its single default Variant
  /// and run the exact same canSell() gate the sheet/side-panel use, then
  /// add it silently. This is still never a bypass of stock checking; it's
  /// only a bypass of the *modal UI*.
  Future<void> _addInstantly(
    List<VariantOptionGroupsTableData> groups,
    List<AddonGroupsTableData> addonGroups,
    List<VariantsTableData> variants,
  ) async {
    final resolvedVariant = resolveSelectedVariant(
      groups: groups,
      variants: variants,
      selectedVariantOptions: const {},
    );
    final db = ref.read(appDatabaseProvider);
    final status = await evaluateAddToCartStatus(
      resolvedVariant: resolvedVariant,
      allGroupsSelected: true,
      quantity: 1,
      inventory: VariantInventory(db),
      cart: ref.read(cartNotifierProvider),
    );
    if (!mounted) return;

    if (status.blocked || resolvedVariant == null) {
      ref.read(posNotifierProvider.notifier).showToast(status.message);
      return;
    }

    ref.read(cartNotifierProvider.notifier).addItem(buildCartItem(
          product: widget.product,
          variant: resolvedVariant,
          groups: groups,
          selectedVariantOptions: const {},
          optionsByGroup: const {},
          addonGroups: addonGroups,
          selectedAddons: const {},
          addonItemsByGroup: const {},
          quantity: 1,
          id: _uuid.v4(),
        ));
    ref
        .read(posNotifierProvider.notifier)
        .showToast('${widget.product.name} added to cart');
  }

  @override
  Widget build(BuildContext context) {
    final price = Decimal.tryParse(widget.product.basePrice) ?? Decimal.zero;
    final money = ref.watch(moneyProvider);
    final displayName = ref
            .watch(componentDisplayNameProvider(widget.product.id))
            .valueOrNull ??
        widget.product.name;

    return GestureDetector(
      onTap: _busy ? null : _handleTap,
      child: Opacity(
        opacity: _busy ? 0.6 : 1,
        child: Container(
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: PosTheme.tileRadius,
            border: Border.all(color: PosTheme.divider),
            boxShadow: PosTheme.shadowSm,
          ),
          child: Stack(
            children: [
              Padding(
                padding: const EdgeInsets.all(10),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(14),
                        child:
                            _QuickTapThumb(imagePath: widget.product.imagePath),
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      displayName,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 13,
                        height: 1.15,
                        fontWeight: FontWeight.w700,
                        color: PosTheme.text,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      money(price),
                      style: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                        color: PosTheme.accent,
                      ),
                    ),
                  ],
                ),
              ),
              if (widget.qtyInCart > 0)
                Positioned(
                  top: 8,
                  right: 8,
                  child: Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                    decoration: const BoxDecoration(
                      color: PosTheme.accentMid,
                      borderRadius: PosTheme.pillRadius,
                    ),
                    child: Text(
                      '${widget.qtyInCart}',
                      style: const TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        color: Colors.white,
                      ),
                    ),
                  ),
                ),
              if (_busy)
                const Positioned.fill(
                  child: Center(
                    child: SizedBox(
                      width: 22,
                      height: 22,
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: PosTheme.accent),
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Bottom sheet — reuses VariantContent, never re-implements it ────────────

class _CustomizationSheet extends StatelessWidget {
  final ProductsTableData product;
  final List<VariantOptionGroupsTableData> groups;
  final List<AddonGroupsTableData> addonGroups;
  final List<VariantsTableData> variants;

  const _CustomizationSheet({
    required this.product,
    required this.groups,
    required this.addonGroups,
    required this.variants,
  });

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: FractionallySizedBox(
        heightFactor: 0.85,
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.only(top: 10, bottom: 4),
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: PosTheme.divider,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            Expanded(
              child: VariantContent(
                product: product,
                groups: groups,
                addonGroups: addonGroups,
                variants: variants,
                onAddedToCart: () => Navigator.of(context).pop(),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Thumbnail / loading / empty states ───────────────────────────────────────

class _QuickTapThumb extends StatelessWidget {
  final String? imagePath;
  const _QuickTapThumb({required this.imagePath});

  @override
  Widget build(BuildContext context) {
    final url = assetUrl(imagePath);
    if (url == null) return const _ThumbPlaceholder();
    return Image.network(
      url,
      fit: BoxFit.cover,
      width: double.infinity,
      height: double.infinity,
      gaplessPlayback: true,
      loadingBuilder: (context, child, progress) =>
          progress == null ? child : const _ThumbPlaceholder(),
      errorBuilder: (context, error, stack) => const _ThumbPlaceholder(),
    );
  }
}

class _ThumbPlaceholder extends StatelessWidget {
  const _ThumbPlaceholder();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      height: double.infinity,
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [PosTheme.neutral200, PosTheme.divider],
        ),
      ),
      child: Icon(
        Icons.fastfood_outlined,
        size: 24,
        color: PosTheme.textMuted.withValues(alpha: 0.5),
      ),
    );
  }
}

class _LoadingGrid extends StatelessWidget {
  const _LoadingGrid();

  @override
  Widget build(BuildContext context) {
    return GridView.builder(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
      gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
        maxCrossAxisExtent: 170,
        crossAxisSpacing: 14,
        mainAxisSpacing: 14,
        childAspectRatio: 0.95,
      ),
      itemCount: 8,
      itemBuilder: (_, __) => Container(
        decoration: const BoxDecoration(
          color: PosTheme.neutral200,
          borderRadius: PosTheme.tileRadius,
        ),
      ),
    );
  }
}

class _EmptyPrompt extends StatelessWidget {
  final IconData icon;
  final String message;

  const _EmptyPrompt({required this.icon, required this.message});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 48, color: PosTheme.neutral200),
          const SizedBox(height: 12),
          Text(
            message,
            style: const TextStyle(fontSize: 14, color: PosTheme.textMuted),
          ),
        ],
      ),
    );
  }
}
