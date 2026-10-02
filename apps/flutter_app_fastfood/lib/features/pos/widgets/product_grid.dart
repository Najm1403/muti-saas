// features/pos/widgets/product_grid.dart
//
// 2-column grid of product cards for the selected category (Step 2).
//
// Reads [productsByCategoryProvider(categoryId)] — null-safe: shows an
// empty-state prompt when no category is selected. Cards show a quantity
// badge (total units across all cart lines for that product).

import 'package:decimal/decimal.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/dio_client.dart' show assetUrl;
import '../../../db/app_database.dart';
import '../../../providers/cart_notifier.dart';
import '../../../providers/currency_provider.dart';
import '../../../providers/menu_provider.dart';
import '../pos_state.dart';
import '../pos_theme.dart';
import 'category_rail.dart' show dealsCategoryId;
import 'deal_builder_sheet.dart';

/// 2-column product card grid for the currently selected category.
///
/// States:
///   • No category selected → [_EmptyPrompt] asking cashier to pick a category.
///   • Loading             → [_LoadingGrid] with ghost card placeholders.
///   • Error               → [_EmptyPrompt] with error icon.
///   • Empty category      → [_EmptyPrompt] with no-food icon.
///   • Data                → scrollable [GridView] of [_ProductCard] widgets.
class ProductGrid extends ConsumerWidget {
  const ProductGrid({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedCategoryId = ref.watch(
      posNotifierProvider.select((s) => s.selectedCategoryId),
    );
    final selectedProductId = ref.watch(
      posNotifierProvider.select((s) => s.selectedProductId),
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

    if (!isSearching && selectedCategoryId == dealsCategoryId) {
      return const _DealGrid();
    }

    final productsAsync = isSearching
        ? ref.watch(searchProductsProvider(searchQuery))
        : ref.watch(productsByCategoryProvider(selectedCategoryId!));
    final cartSnapshot = ref.watch(cartNotifierProvider);

    // Map productId → total cart quantity for badge rendering.
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
            maxCrossAxisExtent: 220,
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
            childAspectRatio: 0.92,
          ),
          itemCount: products.length,
          itemBuilder: (context, index) {
            final product = products[index];
            return _ProductCard(
              product: product,
              isSelected: product.id == selectedProductId,
              qtyInCart: cartQtyMap[product.id] ?? 0,
              onTap: () => ref
                  .read(posNotifierProvider.notifier)
                  .selectProduct(product.id),
            );
          },
        );
      },
    );
  }
}

// ── Deal grid — shown instead of the product grid when the "Deals" pseudo-
// category (category_rail.dart's dealsCategoryId) is selected ──────────────

class _DealGrid extends ConsumerWidget {
  const _DealGrid();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dealsAsync = ref.watch(activeDealsProvider);
    return dealsAsync.when(
      loading: () => const _LoadingGrid(),
      error: (e, _) => const _EmptyPrompt(
        icon: Icons.error_outline,
        message: 'Could not load deals',
      ),
      data: (deals) {
        if (deals.isEmpty) {
          return const _EmptyPrompt(
            icon: Icons.local_offer_outlined,
            message: 'No active deals right now',
          );
        }
        return GridView.builder(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
          gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
            maxCrossAxisExtent: 220,
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
            childAspectRatio: 0.92,
          ),
          itemCount: deals.length,
          itemBuilder: (context, index) => _DealCard(deal: deals[index]),
        );
      },
    );
  }
}

class _DealCard extends ConsumerWidget {
  final DealsTableData deal;
  const _DealCard({required this.deal});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final money = ref.watch(moneyProvider);
    final fixedPrice =
        deal.fixedPrice == null ? null : Decimal.tryParse(deal.fixedPrice!);
    final priceLabel = fixedPrice != null
        ? money(fixedPrice)
        : (deal.discountValue != null && deal.discountType != null
            ? (deal.discountType == 'percent'
                ? '${deal.discountValue}% off'
                : '${money(Decimal.tryParse(deal.discountValue!) ?? Decimal.zero)} off')
            : 'Special offer');

    return GestureDetector(
      onTap: () => showDealBuilderSheet(context, deal),
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: PosTheme.tileRadius,
          border: Border.all(color: PosTheme.divider),
          boxShadow: PosTheme.shadowSm,
        ),
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: ClipRRect(
                borderRadius: BorderRadius.circular(18),
                child: Container(
                  decoration: const BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [PosTheme.accentLight, PosTheme.neutral200],
                    ),
                  ),
                  child: const Center(
                    child: Icon(Icons.local_offer,
                        size: 36, color: PosTheme.accent),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 10),
            Text(
              deal.name,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                fontSize: 13,
                height: 1.2,
                fontWeight: FontWeight.w600,
                color: PosTheme.text,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              priceLabel,
              style: const TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w700,
                color: PosTheme.accent,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Single product card ──────────────────────────────────────────────────────

class _ProductCard extends ConsumerWidget {
  final ProductsTableData product;
  final bool isSelected;
  final int qtyInCart;
  final VoidCallback? onTap;

  const _ProductCard({
    required this.product,
    required this.isSelected,
    required this.qtyInCart,
    required this.onTap,
  });

  /// Real stock, reactively resolved — but ONLY for a product with exactly
  /// one Variant (no Variant Option Groups attached). For a multi-variant
  /// product, "the product's stock" is inherently ambiguous until the
  /// cashier picks a combination, so showing any single number here would
  /// itself be the stale/misleading-price bug pattern — the grid
  /// deliberately shows nothing instead for those, matching the side panel
  /// (and quick-tap sheet), which only ever check the resolved Variant.
  (double?, bool) _stockState(WidgetRef ref) {
    final variants =
        ref.watch(variantsForProductProvider(product.id)).valueOrNull;
    if (variants == null || variants.length != 1) return (null, false);
    final v = variants.first;
    if (!v.sellable) return (null, true);
    if (!v.allowInventoryTracking || !v.tracksInventory) return (null, false);
    final stock = ref.watch(branchStockForVariantProvider(v.id)).valueOrNull;
    final qty = (stock?.quantity ?? 0).toDouble();
    return (qty, qty <= 0);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final price = Decimal.tryParse(product.basePrice) ?? Decimal.zero;
    final money = ref.watch(moneyProvider);
    final displayName =
        ref.watch(componentDisplayNameProvider(product.id)).valueOrNull ??
            product.name;
    final (stockQty, outOfStock) = _stockState(ref);
    // A small fixed threshold keeps the order-picker simple — the low-stock
    // alert level is an admin/reporting concept (Product.low_stock_level),
    // not something the POS card needs to sync just to show "running low".
    final threshold = ref.watch(lowStockThresholdProvider).valueOrNull ?? 5;
    final lowStock = stockQty != null && stockQty > 0 && stockQty <= threshold;

    return GestureDetector(
      onTap: onTap,
      child: Opacity(
        opacity: outOfStock ? 0.5 : 1,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          decoration: BoxDecoration(
            color: isSelected ? PosTheme.accentLight : Colors.white,
            borderRadius: PosTheme.tileRadius,
            border: Border.all(
              color: isSelected ? PosTheme.accent : PosTheme.divider,
              width: isSelected ? 2 : 1,
            ),
            boxShadow: isSelected ? PosTheme.shadowMd : PosTheme.shadowSm,
          ),
          child: Stack(
            children: [
              Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Product photo when synced, otherwise a neutral placeholder.
                    Expanded(
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(18),
                        child: _ProductThumb(imagePath: product.imagePath),
                      ),
                    ),
                    const SizedBox(height: 10),
                    Text(
                      displayName,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        fontSize: 13,
                        height: 1.2,
                        fontWeight: FontWeight.w600,
                        color: isSelected ? PosTheme.accentText : PosTheme.text,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Row(
                      children: [
                        Text(
                          money(price),
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w700,
                            color: isSelected ? PosTheme.accent : PosTheme.text,
                          ),
                        ),
                        const Spacer(),
                        const Text(
                          'Options ›',
                          style: TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.w600,
                            color: PosTheme.textMuted,
                          ),
                        ),
                      ],
                    ),
                    if (outOfStock || lowStock) ...[
                      const SizedBox(height: 3),
                      Text(
                        outOfStock
                            ? 'Out of stock'
                            : 'Only ${stockQty!.toInt()} left',
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.w700,
                          color: outOfStock
                              ? PosTheme.textMuted
                              : const Color(0xFFC2410C),
                        ),
                      ),
                    ],
                  ],
                ),
              ),

              // Cart quantity badge — top-right corner, hidden when count is 0.
              if (qtyInCart > 0)
                Positioned(
                  top: 10,
                  right: 10,
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 3,
                    ),
                    decoration: const BoxDecoration(
                      color: PosTheme.accentMid,
                      borderRadius: PosTheme.pillRadius,
                    ),
                    child: Text(
                      '$qtyInCart',
                      style: const TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        color: Colors.white,
                      ),
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

// ── Product thumbnail ────────────────────────────────────────────────────────

/// Network image for a product, with a neutral placeholder while loading,
/// when there is no image, or when the image fails to load (offline etc.).
class _ProductThumb extends StatelessWidget {
  final String? imagePath;
  const _ProductThumb({required this.imagePath});

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
        size: 26,
        color: PosTheme.textMuted.withValues(alpha: 0.5),
      ),
    );
  }
}

// ── Loading skeleton ─────────────────────────────────────────────────────────

class _LoadingGrid extends StatelessWidget {
  const _LoadingGrid();

  @override
  Widget build(BuildContext context) {
    return GridView.builder(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        crossAxisSpacing: 14,
        mainAxisSpacing: 14,
        childAspectRatio: 1.15,
      ),
      itemCount: 6,
      itemBuilder: (_, __) => Container(
        decoration: const BoxDecoration(
          color: PosTheme.neutral200,
          borderRadius: PosTheme.tileRadius,
        ),
      ),
    );
  }
}

// ── Empty / error prompt ─────────────────────────────────────────────────────

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
            style: const TextStyle(
              fontSize: 14,
              color: PosTheme.textMuted,
            ),
          ),
        ],
      ),
    );
  }
}
