import 'widgets/sync_status_banner.dart';
// features/pos/pos_screen.dart
//
// Main POS order-picker screen — tablet-first layout.
//
// Mirrors the "Order Picker.dc.html" design mock:
//
//   ┌───────────────────────────────────────────────────────────────┐
//   │                       PosHeader (72 px)                        │
//   ├───────────────────────────────────────────────────────────────┤
//   │  ┌─────────────────────────────────────┐  ┌────────────────┐   │
//   │  │  Step 1 — Category                  │  │  Step 3 — …    │   │
//   │  │  CategoryRail                       │  │  VariantPanel  │   │
//   │  │  ─────────────────────────────────  │  │  (360 px)      │   │
//   │  │  Step 2 — Product                   │  │                │   │
//   │  │  ProductGrid (flex)                 │  │                │   │
//   │  └─────────────────────────────────────┘  └────────────────┘   │
//   └───────────────────────────────────────────────────────────────┘
//
// Overlaid above when active: CartOverlay (scrim + slide-in panel).
// Topmost layer: PosToast (centered bottom pill).

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../providers/menu_provider.dart';
import 'pos_theme.dart';
import 'widgets/cart_overlay.dart';
import 'widgets/category_rail.dart';
import 'widgets/pos_header.dart';
import 'widgets/pos_toast.dart';
import 'widgets/product_grid.dart';
import 'widgets/product_search_bar.dart';
import 'widgets/quick_tap_grid.dart';
import 'widgets/variant_panel.dart';

/// Fixed width of the right-side variant/options panel.
const double _kVariantPanelWidth = 360.0;

/// The POS order-picker screen.
///
/// Entry point for the `/pos` route. Assembles all POS sub-widgets into the
/// tablet layout. All interactive state lives in [PosNotifier], [CartNotifier],
/// and [DraftNotifier] — this widget is a pure layout shell.
///
/// Renders one of two layouts per the tenant's Business Template
/// (`template.config.pos.layout`, spec Part C / G4):
///   • `grid_with_variant_picker` (default, also the fallback while the
///     value is still loading) — catalog + a fixed side panel.
///   • `grid_quick_tap` — full-width large tap tiles; customization for
///     products that need it opens a bottom sheet instead of a side panel.
/// Both layouts share the exact same selection/resolution/pricing/stock/
/// cart-construction logic (variant_resolution.dart) — this widget only
/// decides which shell to draw.
class PosScreen extends ConsumerWidget {
  const PosScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final layout = ref.watch(posLayoutProvider).valueOrNull;
    final isQuickTap = layout == 'grid_quick_tap';

    if (MediaQuery.sizeOf(context).width < 800) {
      return Scaffold(
          backgroundColor: PosTheme.bg,
          // The product search field is the only text input on this screen;
          // don't squeeze the whole POS grid to make room for the keyboard —
          // let it float over the bottom instead (see ProductSearchBar).
          resizeToAvoidBottomInset: false,
          body: Stack(children: [
            SafeArea(
                child: Column(children: [
              const PosHeader(),
              const SyncStatusBanner(),
              Expanded(
                  child: isQuickTap
                      ? const Padding(
                          padding: EdgeInsets.all(12),
                          child: Column(
                              crossAxisAlignment: CrossAxisAlignment.stretch,
                              children: [
                                ProductSearchBar(),
                                SizedBox(height: 12),
                                CategoryRail(),
                                SizedBox(height: 12),
                                Expanded(child: QuickTapGrid()),
                              ]))
                      : const SingleChildScrollView(
                          child: Padding(
                              padding: EdgeInsets.all(12),
                              child: Column(
                                  crossAxisAlignment:
                                      CrossAxisAlignment.stretch,
                                  children: [
                                    ProductSearchBar(),
                                    SizedBox(height: 12),
                                    CategoryRail(),
                                    SizedBox(height: 12),
                                    SizedBox(height: 350, child: ProductGrid()),
                                    SizedBox(height: 12),
                                    SizedBox(
                                        height: 440, child: VariantPanel()),
                                  ])))),
            ])),
            const CartOverlay(),
            const PosToast(),
          ]));
    }
    return Scaffold(
      backgroundColor: PosTheme.bg,
      resizeToAvoidBottomInset: false,
      body: Stack(
        children: [
          // ── Base layout ────────────────────────────────────────────────────
          SafeArea(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Top bar: ticket#, cashier name, action buttons.
                const PosHeader(), const SyncStatusBanner(),

                // Main body.
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
                    child: isQuickTap
                        ? const _QuickTapBody()
                        : const _VariantPickerBody(),
                  ),
                ),
              ],
            ),
          ),

          // ── Cart / Drafts overlay ──────────────────────────────────────────
          const CartOverlay(),

          // ── Toast notification (topmost) ───────────────────────────────────
          const PosToast(),
        ],
      ),
    );
  }
}

/// `grid_with_variant_picker` — left catalog card (flex) + fixed-width
/// variant/add-on side panel.
class _VariantPickerBody extends StatelessWidget {
  const _VariantPickerBody();

  @override
  Widget build(BuildContext context) {
    return const Row(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // ── Left: Steps 1 & 2 ──────────────────────────────
        Expanded(
          child: _PaneCard(
            color: PosTheme.surface,
            padding: EdgeInsets.fromLTRB(8, 18, 8, 8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                ProductSearchBar(),
                SizedBox(height: 14),
                _StepLabel('Step 1 — Category'),
                SizedBox(height: 10),
                CategoryRail(),
                SizedBox(height: 16),
                _PaneDivider(),
                SizedBox(height: 16),
                _StepLabel('Step 2 — Product'),
                SizedBox(height: 4),
                Expanded(child: ProductGrid()),
              ],
            ),
          ),
        ),
        SizedBox(width: 16),

        // ── Right: Steps 3 & 4 ─────────────────────────────
        SizedBox(
          width: _kVariantPanelWidth,
          child: _PaneCard(
            color: Colors.white,
            shadow: PosTheme.shadowMd,
            padding: EdgeInsets.zero,
            child: VariantPanel(),
          ),
        ),
      ],
    );
  }
}

/// `grid_quick_tap` — one full-width catalog card; customization (when a
/// product needs it) opens as a bottom sheet instead of a fixed side panel.
class _QuickTapBody extends StatelessWidget {
  const _QuickTapBody();

  @override
  Widget build(BuildContext context) {
    return const _PaneCard(
      color: PosTheme.surface,
      padding: EdgeInsets.fromLTRB(8, 18, 8, 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          ProductSearchBar(),
          SizedBox(height: 14),
          _StepLabel('Step 1 — Category'),
          SizedBox(height: 10),
          CategoryRail(),
          SizedBox(height: 16),
          _PaneDivider(),
          SizedBox(height: 16),
          _StepLabel('Step 2 — Product'),
          SizedBox(height: 4),
          Expanded(child: QuickTapGrid()),
        ],
      ),
    );
  }
}

// ── Shared layout pieces ─────────────────────────────────────────────────────

/// Rounded surface card that wraps a pane (32 px radius, matches the mock).
class _PaneCard extends StatelessWidget {
  final Widget child;
  final Color color;
  final EdgeInsets padding;
  final List<BoxShadow> shadow;

  const _PaneCard({
    required this.child,
    required this.color,
    this.padding = const EdgeInsets.all(16),
    this.shadow = const [],
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        color: color,
        borderRadius: PosTheme.panelRadius,
        boxShadow: shadow,
      ),
      padding: padding,
      child: child,
    );
  }
}

/// Small uppercase "Step N — …" eyebrow label.
class _StepLabel extends StatelessWidget {
  final String text;
  const _StepLabel(this.text);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Text(
        text.toUpperCase(),
        style: const TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w700,
          letterSpacing: 1.4,
          color: PosTheme.accentText,
        ),
      ),
    );
  }
}

/// Hairline divider inset to match the pane's content padding.
class _PaneDivider extends StatelessWidget {
  const _PaneDivider();

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.symmetric(horizontal: 20),
      child: Divider(height: 1, thickness: 1, color: PosTheme.divider),
    );
  }
}
