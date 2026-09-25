// features/pos/widgets/category_rail.dart
//
// Horizontal scrolling row of category tiles (Step 1 of the POS order flow).
//
// Reads [categoriesProvider] (async Drift query). Tapping a tile calls
// PosNotifier.selectCategory(), which also clears any selected product.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../db/app_database.dart';
import '../../../providers/menu_provider.dart';
import '../pos_state.dart';
import '../pos_theme.dart';

/// Horizontally scrolling row of category pill tiles.
///
/// Selected tile: accent background + white text + medium shadow.
/// Unselected tile: neutral surface + dark text + subtle shadow.
/// Loading: ghost placeholder tiles (neutral200 fill).
/// Error: centered muted text message.
class CategoryRail extends ConsumerWidget {
  const CategoryRail({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final categoriesAsync = ref.watch(categoriesProvider);
    // Only rebuild when the selected category ID changes, not on every state change.
    final selectedId = ref.watch(
      posNotifierProvider.select((s) => s.selectedCategoryId),
    );

    return SizedBox(
      height: 48,
      child: categoriesAsync.when(
        loading: () => const _LoadingRail(),
        error: (e, _) => const Center(
          child: Text(
            'Could not load categories',
            style: TextStyle(color: PosTheme.textMuted, fontSize: 13),
          ),
        ),
        data: (categories) => ListView.separated(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.symmetric(horizontal: 20),
          itemCount: categories.length,
          separatorBuilder: (_, __) => const SizedBox(width: 10),
          itemBuilder: (context, index) {
            final cat = categories[index];
            return _CategoryTile(
              category: cat,
              isSelected: cat.id == selectedId,
              onTap: () =>
                  ref.read(posNotifierProvider.notifier).selectCategory(cat.id),
            );
          },
        ),
      ),
    );
  }
}

// ── Single category tile ─────────────────────────────────────────────────────

class _CategoryTile extends StatelessWidget {
  final CategoriesTableData category;
  final bool isSelected;
  final VoidCallback onTap;

  const _CategoryTile({
    required this.category,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final initial =
        category.name.isNotEmpty ? category.name.characters.first.toUpperCase() : '?';

    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.fromLTRB(8, 6, 18, 6),
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: isSelected ? PosTheme.accent : Colors.white,
          borderRadius: PosTheme.pillRadius,
          boxShadow: isSelected ? PosTheme.shadowMd : PosTheme.shadowSm,
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Circular initial badge.
            Container(
              width: 30,
              height: 30,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: isSelected ? Colors.white24 : PosTheme.accent2Pale,
                shape: BoxShape.circle,
              ),
              child: Text(
                initial,
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w800,
                  color: isSelected ? Colors.white : PosTheme.accent2Text,
                ),
              ),
            ),
            const SizedBox(width: 10),
            Text(
              category.name,
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: isSelected ? Colors.white : PosTheme.text,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Loading placeholder row ──────────────────────────────────────────────────

/// Ghost placeholder tiles shown while [categoriesProvider] is loading.
class _LoadingRail extends StatelessWidget {
  const _LoadingRail();

  @override
  Widget build(BuildContext context) {
    return ListView.separated(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 20),
      itemCount: 5,
      separatorBuilder: (_, __) => const SizedBox(width: 10),
      itemBuilder: (_, __) => Container(
        width: 100,
        decoration: const BoxDecoration(
          color: PosTheme.neutral200,
          borderRadius: PosTheme.pillRadius,
        ),
      ),
    );
  }
}
