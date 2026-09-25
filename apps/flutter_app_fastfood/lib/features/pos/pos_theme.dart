// features/pos/pos_theme.dart
//
// Design tokens (colors, radii, shadows) for the POS order-picker screen.
//
// A single source of truth — change a value here and it propagates to every
// POS widget. Widgets import this instead of hard-coding hex values.

import 'package:flutter/material.dart';

/// Static design tokens for the POS screen.
///
/// The accent color matches the [ColorScheme.fromSeed] seed in [FastFoodPosApp]
/// so the POS UI stays consistent with any shared Material widgets (dialogs,
/// snackbars, etc.) that use the theme.
abstract final class PosTheme {
  // ── Primary accent — deep orange (matches app MaterialTheme seed) ──────────

  /// Primary call-to-action color: "Add to cart", "Take payment", selected states.
  static const Color accent = Color(0xFFE65100);

  /// Very light tint — selected tile/card backgrounds.
  static const Color accentLight = Color(0xFFFBE9E7);

  /// Medium tint — quantity badge backgrounds.
  static const Color accentMid = Color(0xFFFF8A65);

  /// Darker shade — pressed / hover states on primary buttons.
  static const Color accentDark = Color(0xFFD84315);

  /// Text on accent-light backgrounds (labels, sub-headings in accent areas).
  static const Color accentText = Color(0xFFBF360C);

  // ── Secondary accent — emerald green (drafts, secondary CTAs) ─────────────

  /// Secondary action color: "Drafts" button, "Resume" badge.
  static const Color accent2 = Color(0xFF059669);

  /// Very light tint — summary boxes, price totals background.
  static const Color accent2Light = Color(0xFFECFDF5);

  /// Light tint — secondary badge backgrounds.
  static const Color accent2Pale = Color(0xFFA7F3D0);

  /// Pressed / hover state on secondary buttons.
  static const Color accent2Dark = Color(0xFF047857);

  /// Dark text on accent2-light backgrounds.
  static const Color accent2Text = Color(0xFF065F46);

  // ── Surfaces & neutrals ───────────────────────────────────────────────────

  /// Page background (slightly warm gray so panels stand out).
  static const Color bg = Colors.white;

  /// Panel / card surface color (left catalog panel, product cards).
  static const Color surface = Color(0xFFF5F5F5);

  /// Lighter surface (right variant panel background).
  static const Color neutral100 = Color(0xFFF5F5F5);

  /// Chip / toggle track background when unselected.
  static const Color neutral200 = Color(0xFFEEEEEE);

  /// Divider lines.
  static const Color divider = Color(0xFFE5E7EB);

  /// Toast background — dark so it floats above all content.
  static const Color neutral900 = Color(0xFF1A1A1A);

  // ── Text ─────────────────────────────────────────────────────────────────

  /// Primary body text.
  static const Color text = Color(0xFF1A1A1A);

  /// Secondary / muted text (hints, metadata).
  static const Color textMuted = Color(0xFF6B7280);

  // ── Border radii ─────────────────────────────────────────────────────────

  /// Product cards and category tiles — 28 px rounded corners.
  static const BorderRadius tileRadius = BorderRadius.all(Radius.circular(28));

  /// Left and right main panels — 32 px rounded corners.
  static const BorderRadius panelRadius =
      BorderRadius.all(Radius.circular(32));

  /// Buttons, badges, chips, toasts — fully rounded pill shape.
  static const BorderRadius pillRadius =
      BorderRadius.all(Radius.circular(999));

  /// Cart overlay panel — rounded only on the left side (flush to right edge).
  static const BorderRadius overlayRadius = BorderRadius.only(
    topLeft: Radius.circular(40),
    bottomLeft: Radius.circular(40),
  );

  // ── Shadows ──────────────────────────────────────────────────────────────

  /// Subtle lift for unselected tiles and panels.
  static const List<BoxShadow> shadowSm = [
    BoxShadow(color: Color(0x14000000), blurRadius: 4, offset: Offset(0, 1)),
  ];

  /// Moderate elevation for the selected/active variant panel.
  static const List<BoxShadow> shadowMd = [
    BoxShadow(color: Color(0x18000000), blurRadius: 8, offset: Offset(0, 2)),
    BoxShadow(color: Color(0x0A000000), blurRadius: 4, offset: Offset(0, 1)),
  ];

  /// Strong lift for the cart/drafts overlay panel.
  static const List<BoxShadow> shadowLg = [
    BoxShadow(color: Color(0x26000000), blurRadius: 32, offset: Offset(-4, 0)),
    BoxShadow(color: Color(0x0F000000), blurRadius: 8, offset: Offset(0, 2)),
  ];
}
