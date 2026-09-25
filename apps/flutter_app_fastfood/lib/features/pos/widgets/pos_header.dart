// features/pos/widgets/pos_header.dart
//
// Top bar for the POS order-picker screen.
//
// Layout (left → right):
//   [Brand circle] [Ticket # / cashier name] ── spacer ── [Sync] [Dashboard] [New Order] [Drafts] [View Cart]

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../providers/auth_notifier.dart';
import '../../../providers/cart_notifier.dart';
import '../../../providers/connectivity_provider.dart';
import '../../../providers/menu_provider.dart';
import '../../../providers/repository_providers.dart';
import '../pos_state.dart';
import '../pos_theme.dart';

/// Fixed 72 px top bar showing the ticket number, cashier name, and CTA buttons.
///
/// Buttons on the right:
///   • Sync      — runs a delta sync against the server; disabled while offline.
///   • Dashboard — returns to the cashier dashboard.
///   • New Order — resets POS state, clears cart, increments ticket counter.
///   • Drafts    — toggles the draft orders overlay; badge shows draft count.
///   • View Cart — toggles the cart review overlay; badge shows item count.
class PosHeader extends ConsumerWidget {
  const PosHeader({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pos = ref.watch(posNotifierProvider);
    final posNotifier = ref.read(posNotifierProvider.notifier);
    final drafts = ref.watch(draftNotifierProvider);
    final cartSnapshot = ref.watch(cartNotifierProvider);
    final authAsync = ref.watch(authNotifierProvider);
    final ticketNumber = ref.watch(ticketCounterProvider);

    // Cashier name falls back to em-dash while auth is still loading.
    final cashierName = authAsync.valueOrNull?.cashierName ?? '—';

    // Sum all item quantities for the cart badge count.
    final cartItemCount = cartSnapshot.items.fold<int>(
      0,
      (sum, item) => sum + item.quantity.toBigInt().toInt(),
    );

    if (MediaQuery.sizeOf(context).width < 800) {
      return SizedBox(
          height: 64,
          child: Row(children: [
            const _SyncIconButton(),
            IconButton(
                tooltip: 'Dashboard',
                icon: const Icon(Icons.dashboard_outlined),
                onPressed: () => context.go('/dashboard')),
            Expanded(
                child: Text('Ticket #$ticketNumber',
                    overflow: TextOverflow.ellipsis)),
            IconButton(
                tooltip: 'New order',
                icon: const Icon(Icons.add),
                onPressed: () {
                  ref.read(ticketCounterProvider.notifier).state =
                      ticketNumber + 1;
                  posNotifier.resetAll();
                  ref.read(cartNotifierProvider.notifier).clear();
                }),
            IconButton(
                tooltip: 'Drafts (${drafts.length})',
                icon: const Icon(Icons.bookmark_outline),
                onPressed: posNotifier.openDrafts),
            IconButton(
                tooltip: 'Cart ($cartItemCount)',
                icon: const Icon(Icons.shopping_cart_outlined),
                onPressed: posNotifier.openCart),
          ]));
    }
    return Container(
      height: 72,
      padding: const EdgeInsets.symmetric(horizontal: 20),
      decoration: const BoxDecoration(
        color: PosTheme.bg,
        border: Border(
          bottom: BorderSide(color: PosTheme.divider, width: 1),
        ),
      ),
      child: Row(
        children: [
          // ── Brand circle ──────────────────────────────────────────────────
          Container(
            width: 44,
            height: 44,
            decoration: const BoxDecoration(
              color: PosTheme.accent,
              borderRadius: PosTheme.pillRadius,
            ),
            padding: const EdgeInsets.all(5),
            child: Image.asset('assets/smartshop.png',
                fit: BoxFit.contain, semanticLabel: 'Storixx'),
          ),
          const SizedBox(width: 14),

          // ── Ticket number and cashier name ────────────────────────────────
          Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Ticket #$ticketNumber',
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                  color: PosTheme.text,
                ),
              ),
              Text(
                cashierName,
                style: const TextStyle(
                  fontSize: 12,
                  color: PosTheme.textMuted,
                ),
              ),
            ],
          ),

          // ── Spacer pushes buttons to the right ────────────────────────────
          const Spacer(),

          // ── Sync (delta sync against the server) ─────────────────────────
          const _SyncButton(),
          const SizedBox(width: 10),

          _HeaderButton(
            label: 'Dashboard',
            icon: Icons.dashboard_outlined,
            color: PosTheme.text,
            onTap: () => context.go('/dashboard'),
          ),
          const SizedBox(width: 10),

          // ── New Order ────────────────────────────────────────────────────
          _HeaderButton(
            label: 'New Order',
            icon: Icons.add_circle_outline,
            color: PosTheme.accent,
            onTap: () {
              ref.read(ticketCounterProvider.notifier).state = ticketNumber + 1;
              posNotifier.resetAll();
              ref.read(cartNotifierProvider.notifier).clear();
            },
          ),
          const SizedBox(width: 10),

          // ── Drafts (toggling, badge shows draft count) ───────────────────
          _BadgedButton(
            label: 'Drafts',
            icon: Icons.bookmark_outline,
            color: PosTheme.accent2,
            badgeCount: drafts.length,
            isActive: pos.overlay == PosOverlay.drafts,
            onTap: () {
              if (pos.overlay == PosOverlay.drafts) {
                posNotifier.closeOverlay();
              } else {
                posNotifier.openDrafts();
              }
            },
          ),
          const SizedBox(width: 10),

          // ── View Cart (toggling, badge shows cart item count) ────────────
          _BadgedButton(
            label: 'View Cart',
            icon: Icons.shopping_cart_outlined,
            color: PosTheme.accent,
            badgeCount: cartItemCount,
            isActive: pos.overlay == PosOverlay.cart,
            onTap: () {
              if (pos.overlay == PosOverlay.cart) {
                posNotifier.closeOverlay();
              } else {
                posNotifier.openCart();
              }
            },
          ),
        ],
      ),
    );
  }
}

// ── Sync ──────────────────────────────────────────────────────────────────

/// Runs a delta sync and invalidates the menu/stock caches so freshly synced
/// data shows up immediately — the same invalidation list as the Settings
/// screen's own "Sync now" button (features/settings/settings_screen.dart).
Future<void> _runDeltaSync(WidgetRef ref) async {
  await ref.read(syncRepositoryProvider).deltaSync();
  ref.invalidate(categoriesProvider);
  ref.invalidate(allActiveProductsProvider);
  ref.invalidate(productStockProvider);
  ref.invalidate(lowStockThresholdProvider);
  ref.invalidate(lowStockCountProvider);
}

/// Wide-header "Sync" pill — first button before Dashboard, matching the
/// other header buttons' look. Disabled while offline or already syncing.
class _SyncButton extends ConsumerStatefulWidget {
  const _SyncButton();

  @override
  ConsumerState<_SyncButton> createState() => _SyncButtonState();
}

class _SyncButtonState extends ConsumerState<_SyncButton> {
  bool _syncing = false;

  Future<void> _tap() async {
    setState(() => _syncing = true);
    try {
      await _runDeltaSync(ref);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Sync complete'),
          backgroundColor: Colors.green,
          duration: Duration(seconds: 2)));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('Sync failed: $e'), backgroundColor: Colors.red));
    } finally {
      if (mounted) setState(() => _syncing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final online = ref.watch(connectivityProvider).valueOrNull ?? false;
    final enabled = online && !_syncing;
    final color = enabled ? PosTheme.text : PosTheme.textMuted;

    return GestureDetector(
      onTap: enabled ? _tap : null,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.1),
          borderRadius: PosTheme.pillRadius,
        ),
        child: Row(
          children: [
            _syncing
                ? SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(
                        strokeWidth: 2, color: color),
                  )
                : Icon(Icons.sync, size: 18, color: color),
            const SizedBox(width: 6),
            Text(
              online ? 'Sync' : 'Offline',
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: color,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Narrow-header icon-only equivalent of [_SyncButton].
class _SyncIconButton extends ConsumerStatefulWidget {
  const _SyncIconButton();

  @override
  ConsumerState<_SyncIconButton> createState() => _SyncIconButtonState();
}

class _SyncIconButtonState extends ConsumerState<_SyncIconButton> {
  bool _syncing = false;

  Future<void> _tap() async {
    setState(() => _syncing = true);
    try {
      await _runDeltaSync(ref);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Sync complete'),
          backgroundColor: Colors.green,
          duration: Duration(seconds: 2)));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('Sync failed: $e'), backgroundColor: Colors.red));
    } finally {
      if (mounted) setState(() => _syncing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final online = ref.watch(connectivityProvider).valueOrNull ?? false;
    final enabled = online && !_syncing;
    return IconButton(
      tooltip: online ? 'Sync' : 'Offline',
      icon: _syncing
          ? const SizedBox(
              width: 18,
              height: 18,
              child: CircularProgressIndicator(strokeWidth: 2))
          : const Icon(Icons.sync),
      onPressed: enabled ? _tap : null,
    );
  }
}

// ── Private button widgets ───────────────────────────────────────────────────

/// Pill-shaped header button without a badge.
class _HeaderButton extends StatelessWidget {
  final String label;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;

  const _HeaderButton({
    required this.label,
    required this.icon,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.1),
          borderRadius: PosTheme.pillRadius,
        ),
        child: Row(
          children: [
            Icon(icon, size: 18, color: color),
            const SizedBox(width: 6),
            Text(
              label,
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: color,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Pill-shaped header button with an item count badge.
///
/// When [isActive] is true the background is solid [color] (inverted style)
/// so the cashier can tell at a glance which overlay is open.
/// The badge is hidden when [badgeCount] is zero.
class _BadgedButton extends StatelessWidget {
  final String label;
  final IconData icon;
  final Color color;
  final int badgeCount;
  final bool isActive;
  final VoidCallback onTap;

  const _BadgedButton({
    required this.label,
    required this.icon,
    required this.color,
    required this.badgeCount,
    required this.isActive,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final bg = isActive ? color : color.withValues(alpha: 0.1);
    final fg = isActive ? Colors.white : color;

    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          color: bg,
          borderRadius: PosTheme.pillRadius,
        ),
        child: Row(
          children: [
            Icon(icon, size: 18, color: fg),
            const SizedBox(width: 6),
            Text(
              label,
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: fg,
              ),
            ),
            // Badge — only shown when count > 0.
            if (badgeCount > 0) ...[
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                decoration: BoxDecoration(
                  // On active (inverted) button use semi-transparent white;
                  // on normal button use solid color so badge pops.
                  color: isActive ? Colors.white24 : color,
                  borderRadius: PosTheme.pillRadius,
                ),
                child: Text(
                  '$badgeCount',
                  style: const TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    color: Colors.white,
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
