// features/pos/widgets/cart_overlay.dart
//
// Full-height slide-in overlay from the right edge of the screen.
// Shows either:
//   • Cart review  (PosOverlay.cart)   — items, totals, Take Payment, Park as Draft
//   • Draft orders (PosOverlay.drafts) — parked order tiles with Resume / Discard
//
// The overlay sits in a Stack that covers the entire screen. A semi-transparent
// scrim fills the rest of the width and closes the overlay when tapped.

import 'package:decimal/decimal.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../features/sale/cart_service.dart';
import '../../../providers/cart_notifier.dart';
import '../../../providers/currency_provider.dart';
import '../../../providers/discount_eligibility_provider.dart' show discountEligibilityProvider, discountPermissionProvider;
import '../pos_state.dart';
import '../../../providers/dio_provider.dart';
import 'package:uuid/uuid.dart';
import '../pos_theme.dart';

/// Animated slide-in overlay (cart or drafts view).
///
/// Must be placed as a child of the root [Stack] in [PosScreen] so it covers
/// the full screen. Uses [AnimatedSwitcher] for fade in/out; the inner panel
/// uses [TweenAnimationBuilder] for a translate-from-right entrance.
class CartOverlay extends ConsumerWidget {
  const CartOverlay({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final overlay = ref.watch(
      posNotifierProvider.select((s) => s.overlay),
    );

    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 260),
      transitionBuilder: (child, animation) =>
          FadeTransition(opacity: animation, child: child),
      child: overlay != PosOverlay.none
          ? _OverlayContent(key: const ValueKey('overlay'), overlay: overlay)
          : const SizedBox.shrink(key: ValueKey('hidden')),
    );
  }
}

// ── Overlay shell ────────────────────────────────────────────────────────────

class _OverlayContent extends ConsumerWidget {
  final PosOverlay overlay;
  const _OverlayContent({required this.overlay, super.key});

  static const double _panelWidth = 460;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final posNotifier = ref.read(posNotifierProvider.notifier);

    return Stack(
      children: [
        // Scrim — tapping dismisses the overlay.
        GestureDetector(
          onTap: posNotifier.closeOverlay,
          child: Container(color: Colors.black38),
        ),

        // Panel slides in from the right edge.
        Positioned(
          top: 0,
          right: 0,
          bottom: 0,
          width: MediaQuery.sizeOf(context).width.clamp(0, _panelWidth).toDouble(),
          child: TweenAnimationBuilder<double>(
            tween: Tween(begin: _panelWidth, end: 0),
            duration: const Duration(milliseconds: 260),
            curve: Curves.easeOut,
            builder: (_, dx, child) =>
                Transform.translate(offset: Offset(dx, 0), child: child),
            child: Container(
              decoration: const BoxDecoration(
                color: Colors.white,
                borderRadius: PosTheme.overlayRadius,
                boxShadow: PosTheme.shadowLg,
              ),
              child: overlay == PosOverlay.cart
                  ? const _CartView()
                  : const _DraftsView(),
            ),
          ),
        ),
      ],
    );
  }
}

// ── Cart view ────────────────────────────────────────────────────────────────

class _CartView extends ConsumerWidget {
  const _CartView();

  Future<void> _offers(BuildContext context, WidgetRef ref) async {
    final code = TextEditingController();
    final supplied = await showDialog<String>(context: context, builder: (dialogContext) => AlertDialog(
      title: const Text('Apply an offer'), content: TextField(controller: code,
        decoration: const InputDecoration(labelText: 'Promo code (optional)')),
      actions: [TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('Cancel')),
        FilledButton(onPressed: () => Navigator.pop(dialogContext, code.text.trim()), child: const Text('Find offers'))]));
    // Deferred for the same reason as _applyDiscount's amountCtrl below —
    // the dialog's exit transition still touches the TextField for one
    // more frame after showDialog's future resolves.
    WidgetsBinding.instance.addPostFrameCallback((_) => code.dispose());
    if (supplied == null || !context.mounted) return;
    final snapshot = ref.read(cartNotifierProvider);
    try {
      final response = await ref.read(dioProvider).post('/api/v1/pos/sales/offers/preview',
        data: snapshot.toPosSaleCreate(id: const Uuid().v4(), saleNumber: 'QUOTE').toJson(),
        queryParameters: {'promo_code':supplied});
      final offers = response.data as List;
      if (!context.mounted) return;
      final chosen = await showDialog<Map<String,dynamic>>(context: context, builder: (dialogContext) => AlertDialog(
        title: const Text('Available offers'), content: SizedBox(width: 380, child: offers.isEmpty
          ? const Text('No matching offers. Add the required bundle items or check the promo code.')
          : ListView(shrinkWrap:true, children: offers.map((o) => ListTile(title:Text(o['name']),
              subtitle:Text('Discount: ${o['discount']}'), onTap:()=>Navigator.pop(dialogContext,Map<String,dynamic>.from(o)))).toList())),
        actions:[TextButton(onPressed:()=>Navigator.pop(dialogContext),child:const Text('Close'))]));
      if (chosen == null || !context.mounted) return;
      if (!identical(snapshot, ref.read(cartNotifierProvider))) {
        ref.read(posNotifierProvider.notifier).showToast('Cart changed. Find offers again.'); return;
      }
      final cart = ref.read(cartNotifierProvider.notifier);
      for (final reward in chosen['rewards'] as List) {
        final variantId = reward['variant_id'] as String?;
        if (variantId == null) {
          ref.read(posNotifierProvider.notifier).showToast(
              'Reward item has no default variant. Sync and try again.');
          continue;
        }
        cart.addItem(CartItem(id:const Uuid().v4(),variantId:variantId,productId:reward['product_id'],
          productName:reward['product_name'],unitPrice:Decimal.parse(reward['unit_price']),quantity:Decimal.parse(reward['quantity'])));
      }
      cart.setPromotion(chosen['kind']=='promotion'?chosen['id']:null);
      cart.setDeal(chosen['kind']=='deal'?chosen['id']:null);
      cart.setDiscount(Decimal.parse(chosen['discount']));
      ref.read(posNotifierProvider.notifier).showToast('Offer applied');
    } catch (error) {
      if (context.mounted) ref.read(posNotifierProvider.notifier).showToast(error.toString());
    }
  }

  /// Manual, cashier-entered discount — gated by the `sales.discount`
  /// permission (the button that opens this is only shown when
  /// [discountEligibilityProvider] is true; the server re-checks it too,
  /// see services/offer_service.py::OfferService.validate). Distinct from
  /// "Offers and deals" above: applying one here always clears any active
  /// Promotion/Deal (setPromotion/setDeal to null) so the two never
  /// silently combine — cart.discount always reflects exactly one source.
  Future<void> _applyDiscount(BuildContext context, WidgetRef ref) async {
    final snapshot = ref.read(cartNotifierProvider);
    final money = ref.read(moneyProvider);
    final capPercent =
        ref.read(discountPermissionProvider).valueOrNull?.maxPercent;
    var isPercent = true;
    final amountCtrl = TextEditingController(
      text: snapshot.promotionId == null && snapshot.dealId == null && snapshot.discount > Decimal.zero
          ? snapshot.discount.toString()
          : '',
    );
    final applied = await showDialog<Decimal>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(builder: (dialogContext, setState) {
        final subtotal = snapshot.subtotal.toDouble();
        // The cap is always expressed as a percent of subtotal, regardless
        // of whether the cashier is entering a percent or a fixed amount —
        // see User.max_discount_percent / services/offer_service.py.
        final maxAllowed =
            capPercent == null ? subtotal : subtotal * capPercent.toDouble() / 100;
        final entered = double.tryParse(amountCtrl.text) ?? 0;
        final rawAmount = isPercent ? subtotal * entered / 100 : entered;
        final cappedAmount = rawAmount.clamp(0, maxAllowed).toDouble();
        final cappedDecimal = Decimal.parse(cappedAmount.toStringAsFixed(2));
        final newTotal = snapshot.subtotal - cappedDecimal;
        final hitCap = rawAmount > maxAllowed;
        return AlertDialog(
          title: const Text('Apply Discount'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SegmentedButton<bool>(
                segments: const [
                  ButtonSegment(value: true, label: Text('Percent')),
                  ButtonSegment(value: false, label: Text('Fixed amount')),
                ],
                selected: {isPercent},
                onSelectionChanged: (s) => setState(() => isPercent = s.first),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: amountCtrl,
                autofocus: true,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: InputDecoration(
                  labelText: isPercent ? 'Discount %' : 'Discount amount',
                  border: const OutlineInputBorder(),
                ),
                onChanged: (_) => setState(() {}),
              ),
              if (capPercent != null) ...[
                const SizedBox(height: 6),
                Text('Your maximum: $capPercent% (${money(maxAllowed)})',
                    style: const TextStyle(fontSize: 12, color: PosTheme.textMuted)),
              ],
              if (hitCap)
                const Padding(
                  padding: EdgeInsets.only(top: 4),
                  child: Text('Capped at your maximum discount.',
                      style: TextStyle(fontSize: 12, color: PosTheme.accent)),
                ),
              const SizedBox(height: 12),
              Text('New total: ${money(newTotal)}',
                  style: const TextStyle(fontWeight: FontWeight.w600)),
            ],
          ),
          actions: [
            if (snapshot.discount > Decimal.zero && snapshot.promotionId == null && snapshot.dealId == null)
              TextButton(
                onPressed: () => Navigator.pop(dialogContext, Decimal.zero),
                child: const Text('Remove discount'),
              ),
            TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('Cancel')),
            FilledButton(
              onPressed: entered <= 0 ? null : () => Navigator.pop(dialogContext, cappedDecimal),
              child: const Text('Apply'),
            ),
          ],
        );
      }),
    );
    // Deferred: the dialog's exit transition keeps the TextField (and its
    // controller listener) mounted for one more frame after showDialog's
    // future resolves — disposing synchronously here races that teardown.
    WidgetsBinding.instance.addPostFrameCallback((_) => amountCtrl.dispose());
    if (applied == null || !context.mounted) return;
    if (!identical(snapshot, ref.read(cartNotifierProvider))) {
      ref.read(posNotifierProvider.notifier).showToast('Cart changed. Apply the discount again.');
      return;
    }
    final cart = ref.read(cartNotifierProvider.notifier);
    cart.setPromotion(null);
    cart.setDeal(null);
    cart.setDiscount(applied);
    ref.read(posNotifierProvider.notifier).showToast(
        applied > Decimal.zero ? 'Discount applied' : 'Discount removed');
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final cartSnapshot = ref.watch(cartNotifierProvider);
    final cartNotifier = ref.read(cartNotifierProvider.notifier);
    final posNotifier = ref.read(posNotifierProvider.notifier);
    final draftNotifier = ref.read(draftNotifierProvider.notifier);
    final ticketNumber = ref.watch(ticketCounterProvider);
    final items = cartSnapshot.items;

    return Column(
      children: [
        _PanelTopBar(
          title: 'Cart',
          subtitle: '${items.length} item${items.length == 1 ? '' : 's'}',
          onClose: posNotifier.closeOverlay,
        ),

        // Item list — components are grouped directly under the base line
        // they were selected for (Laptop Store shareable-inventory model),
        // regardless of raw insertion order (see [_groupedForCartDisplay]).
        Expanded(
          child: items.isEmpty
              ? const _EmptyCartPrompt()
              : Builder(builder: (_) {
                  final ordered = _groupedForCartDisplay(items);
                  return ListView.separated(
                    padding: const EdgeInsets.all(16),
                    itemCount: ordered.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 10),
                    itemBuilder: (_, i) => _CartItemTile(
                      item: ordered[i],
                      isComponent: ordered[i].parentCartItemId != null,
                      onRemove: () => cartNotifier.removeItem(ordered[i].id),
                    ),
                  );
                }),
        ),

        if (items.isNotEmpty)
          Wrap(
            children: [
              TextButton.icon(onPressed: () => _offers(context, ref), icon: const Icon(Icons.local_offer_outlined), label: const Text('Offers and deals')),
              if (ref.watch(discountEligibilityProvider).valueOrNull ?? false)
                TextButton.icon(onPressed: () => _applyDiscount(context, ref), icon: const Icon(Icons.percent_outlined), label: const Text('Apply Discount')),
            ],
          ),
        // Totals + action buttons — only rendered when cart has items.
        if (items.isNotEmpty)
          _CartFooter(
            cartSnapshot: cartSnapshot,
            onPark: () {
              draftNotifier.park(
                ticketLabel: 'Ticket #$ticketNumber',
                items: List.from(items),
                taxRate: cartSnapshot.taxRate,
                taxInclusive: cartSnapshot.taxInclusive,
              );
              cartNotifier.clear();
              posNotifier.closeOverlay();
              posNotifier.showToast('Order parked as draft');
            },
            onCheckout: () {
              posNotifier.closeOverlay();
              context.push('/pos/checkout');
            },
          ),
      ],
    );
  }
}

// ── Drafts view ──────────────────────────────────────────────────────────────

class _DraftsView extends ConsumerWidget {
  const _DraftsView();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final draftList = ref.watch(draftNotifierProvider);
    final draftNotifier = ref.read(draftNotifierProvider.notifier);
    final cartNotifier = ref.read(cartNotifierProvider.notifier);
    final posNotifier = ref.read(posNotifierProvider.notifier);

    return Column(
      children: [
        _PanelTopBar(
          title: 'Drafts',
          subtitle:
              '${draftList.length} parked order${draftList.length == 1 ? '' : 's'}',
          onClose: posNotifier.closeOverlay,
        ),
        Expanded(
          child: draftList.isEmpty
              ? const Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.bookmark_border,
                          size: 48, color: PosTheme.neutral200),
                      SizedBox(height: 12),
                      Text(
                        'No parked orders',
                        style: TextStyle(
                            color: PosTheme.textMuted, fontSize: 14),
                      ),
                    ],
                  ),
                )
              : ListView.separated(
                  padding: const EdgeInsets.all(16),
                  itemCount: draftList.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 10),
                  itemBuilder: (_, i) {
                    final draft = draftList[i];
                    return _DraftTile(
                      draft: draft,
                      onResume: () {
                        // Load draft items into cart, delete draft, close overlay.
                        cartNotifier.clear();
                        cartNotifier.addItems(draft.items);
                        cartNotifier.setTax(
                          rate: draft.taxRate,
                          inclusive: draft.taxInclusive,
                        );
                        draftNotifier.remove(draft.id);
                        posNotifier.closeOverlay();
                        posNotifier.showToast('Draft loaded into cart');
                      },
                      onDiscard: () => draftNotifier.remove(draft.id),
                    );
                  },
                ),
        ),
      ],
    );
  }
}

// ── Shared panel sub-widgets ─────────────────────────────────────────────────

class _PanelTopBar extends StatelessWidget {
  final String title;
  final String subtitle;
  final VoidCallback onClose;

  const _PanelTopBar({
    required this.title,
    required this.subtitle,
    required this.onClose,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 24, 16, 16),
      decoration: const BoxDecoration(
        border: Border(
          bottom: BorderSide(color: PosTheme.divider, width: 1),
        ),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.w700,
                    color: PosTheme.text,
                  ),
                ),
                Text(
                  subtitle,
                  style: const TextStyle(
                    fontSize: 13,
                    color: PosTheme.textMuted,
                  ),
                ),
              ],
            ),
          ),
          GestureDetector(
            onTap: onClose,
            child: Container(
              width: 36,
              height: 36,
              decoration: const BoxDecoration(
                color: PosTheme.surface,
                borderRadius: PosTheme.pillRadius,
              ),
              child: const Icon(Icons.close, size: 18, color: PosTheme.text),
            ),
          ),
        ],
      ),
    );
  }
}

/// Reorders [items] so each Inventory Component line (see
/// [CartItem.parentCartItemId]) is placed directly after the base line it
/// was selected for, regardless of raw list order — a component added on a
/// later merge of the same base product lands at the end of [items], not
/// next to its parent, so this can't just rely on insertion order.
/// A component whose parent is missing (should not happen once
/// [CartService.removeItem] cascades, kept defensively) is still shown, at
/// the end, rather than silently dropped.
List<CartItem> _groupedForCartDisplay(List<CartItem> items) {
  final byParent = <String, List<CartItem>>{};
  final orphans = <CartItem>[];
  for (final item in items) {
    final parentId = item.parentCartItemId;
    if (parentId == null) continue;
    if (items.any((i) => i.id == parentId)) {
      byParent.putIfAbsent(parentId, () => []).add(item);
    } else {
      orphans.add(item);
    }
  }
  final ordered = <CartItem>[];
  for (final item in items) {
    if (item.parentCartItemId != null) continue;
    ordered.add(item);
    ordered.addAll(byParent[item.id] ?? const []);
  }
  ordered.addAll(orphans);
  return ordered;
}

class _CartItemTile extends ConsumerWidget {
  final CartItem item;
  final bool isComponent;
  final VoidCallback onRemove;

  const _CartItemTile({
    required this.item,
    this.isComponent = false,
    required this.onRemove,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final money = ref.watch(moneyProvider);
    return Container(
      margin: isComponent ? const EdgeInsets.only(left: 28) : EdgeInsets.zero,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isComponent ? PosTheme.bg : PosTheme.surface,
        borderRadius: const BorderRadius.all(Radius.circular(12)),
        border: isComponent
            ? Border.all(color: PosTheme.accentMid.withValues(alpha: 0.3))
            : null,
      ),
      child: Row(
        children: [
          if (isComponent) ...[
            const Icon(Icons.subdirectory_arrow_right,
                size: 16, color: PosTheme.textMuted),
            const SizedBox(width: 6),
          ],
          // Quantity bubble
          Container(
            width: 36,
            height: 36,
            decoration: const BoxDecoration(
              color: PosTheme.accentMid,
              borderRadius: PosTheme.pillRadius,
            ),
            alignment: Alignment.center,
            child: Text(
              '${item.quantity.toBigInt().toInt()}×',
              style: const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w700,
                color: Colors.white,
              ),
            ),
          ),
          const SizedBox(width: 10),
          // Name and selected options
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.productName,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: PosTheme.text,
                  ),
                ),
                if (item.variantOptions.isNotEmpty || item.addons.isNotEmpty)
                  Text(
                    [
                      ...item.variantOptions.map((o) => o.optionName),
                      ...item.addons
                          .where((a) => !a.wasRemoved)
                          .map((a) => a.addonName),
                      ...item.addons
                          .where((a) => a.wasRemoved)
                          .map((a) => 'No ${a.addonName}'),
                    ].join(', '),
                    style: const TextStyle(
                      fontSize: 11,
                      color: PosTheme.textMuted,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
              ],
            ),
          ),
          // Line total
          Text(
            money(item.lineTotal),
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: PosTheme.text,
            ),
          ),
          const SizedBox(width: 8),
          GestureDetector(
            onTap: onRemove,
            child:
                const Icon(Icons.close, size: 16, color: PosTheme.textMuted),
          ),
        ],
      ),
    );
  }
}

class _CartFooter extends StatelessWidget {
  final CartSnapshot cartSnapshot;
  final VoidCallback onPark;
  final VoidCallback onCheckout;

  const _CartFooter({
    required this.cartSnapshot,
    required this.onPark,
    required this.onCheckout,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: const BoxDecoration(
        border: Border(top: BorderSide(color: PosTheme.divider, width: 1)),
      ),
      child: Column(
        children: [
          _TotalRow(label: 'Subtotal', value: cartSnapshot.subtotal),
          if (cartSnapshot.discount > Decimal.zero)
            _TotalRow(
              label: 'Discount',
              value: cartSnapshot.discount,
              isDiscount: true,
            ),
          if (cartSnapshot.taxAmount > Decimal.zero)
            _TotalRow(label: 'Tax', value: cartSnapshot.taxAmount),
          const Divider(color: PosTheme.divider, height: 20),
          _TotalRow(
            label: 'Total',
            value: cartSnapshot.total,
            isBold: true,
            fontSize: 18,
          ),
          const SizedBox(height: 16),

          // Park as Draft — secondary green button.
          GestureDetector(
            onTap: onPark,
            child: Container(
              height: 44,
              decoration: BoxDecoration(
                color: PosTheme.accent2Light,
                borderRadius: PosTheme.pillRadius,
                border: Border.all(color: PosTheme.accent2),
              ),
              alignment: Alignment.center,
              child: const Text(
                'Park as Draft',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: PosTheme.accent2Text,
                ),
              ),
            ),
          ),
          const SizedBox(height: 10),

          // Take Payment — primary orange button.
          GestureDetector(
            onTap: onCheckout,
            child: Container(
              height: 52,
              decoration: const BoxDecoration(
                color: PosTheme.accent,
                borderRadius: PosTheme.pillRadius,
                boxShadow: PosTheme.shadowMd,
              ),
              alignment: Alignment.center,
              child: const Text(
                'Take Payment',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                  color: Colors.white,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// One row in the cart totals section.
class _TotalRow extends ConsumerWidget {
  final String label;
  final Decimal value;
  final bool isDiscount;
  final bool isBold;
  final double fontSize;

  const _TotalRow({
    required this.label,
    required this.value,
    this.isDiscount = false,
    this.isBold = false,
    this.fontSize = 14,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final money = ref.watch(moneyProvider);
    final valueStr = isDiscount ? '-${money(value)}' : money(value);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: TextStyle(
              fontSize: fontSize,
              fontWeight: isBold ? FontWeight.w700 : FontWeight.w400,
              color: PosTheme.textMuted,
            ),
          ),
          Text(
            valueStr,
            style: TextStyle(
              fontSize: fontSize,
              fontWeight: isBold ? FontWeight.w700 : FontWeight.w600,
              color: isDiscount ? PosTheme.accent2 : PosTheme.text,
            ),
          ),
        ],
      ),
    );
  }
}

class _DraftTile extends ConsumerWidget {
  final DraftOrder draft;
  final VoidCallback onResume;
  final VoidCallback onDiscard;

  const _DraftTile({
    required this.draft,
    required this.onResume,
    required this.onDiscard,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final money = ref.watch(moneyProvider);
    final itemCount = draft.items.fold<int>(
      0,
      (sum, item) => sum + item.quantity.toBigInt().toInt(),
    );
    final total = draft.items.fold<Decimal>(
      Decimal.zero,
      (sum, item) => sum + item.lineTotal,
    );
    final timeStr =
        '${draft.createdAt.hour}:${draft.createdAt.minute.toString().padLeft(2, '0')}';

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: PosTheme.accent2Light,
        borderRadius: const BorderRadius.all(Radius.circular(12)),
        border: Border.all(color: PosTheme.accent2Pale),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  draft.label,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: PosTheme.accent2Text,
                  ),
                ),
              ),
              Text(
                timeStr,
                style: const TextStyle(fontSize: 12, color: PosTheme.textMuted),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            '$itemCount item${itemCount == 1 ? '' : 's'} · ${money(total)}',
            style: const TextStyle(fontSize: 12, color: PosTheme.accent2),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: GestureDetector(
                  onTap: onResume,
                  child: Container(
                    height: 36,
                    decoration: const BoxDecoration(
                      color: PosTheme.accent2,
                      borderRadius: PosTheme.pillRadius,
                    ),
                    alignment: Alignment.center,
                    child: const Text(
                      'Resume',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                        color: Colors.white,
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              GestureDetector(
                onTap: onDiscard,
                child: Container(
                  height: 36,
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  decoration: BoxDecoration(
                    color: PosTheme.surface,
                    borderRadius: PosTheme.pillRadius,
                    border: Border.all(color: PosTheme.divider),
                  ),
                  alignment: Alignment.center,
                  child: const Text(
                    'Discard',
                    style: TextStyle(fontSize: 13, color: PosTheme.textMuted),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _EmptyCartPrompt extends StatelessWidget {
  const _EmptyCartPrompt();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.shopping_cart_outlined,
              size: 48, color: PosTheme.neutral200),
          SizedBox(height: 12),
          Text(
            'Cart is empty',
            style: TextStyle(color: PosTheme.textMuted, fontSize: 14),
          ),
        ],
      ),
    );
  }
}
