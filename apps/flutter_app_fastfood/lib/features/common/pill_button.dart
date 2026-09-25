import 'package:flutter/material.dart';

import '../pos/pos_theme.dart';

/// Full-width pill button in the app accent, with a busy spinner state.
///
/// Shared by the onboarding / staff / shift / settings screens.
class PillButton extends StatelessWidget {
  final String label;
  final VoidCallback? onTap;
  final bool loading;
  final bool secondary;
  final IconData? icon;

  const PillButton({
    super.key,
    required this.label,
    required this.onTap,
    this.loading = false,
    this.secondary = false,
    this.icon,
  });

  @override
  Widget build(BuildContext context) {
    final enabled = onTap != null && !loading;
    final bg = secondary
        ? Colors.transparent
        : (enabled ? PosTheme.accent : PosTheme.neutral200);
    final fg = secondary ? PosTheme.text : Colors.white;

    return GestureDetector(
      onTap: enabled ? onTap : null,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        height: 54,
        decoration: BoxDecoration(
          color: bg,
          borderRadius: PosTheme.pillRadius,
          border: secondary
              ? Border.all(color: PosTheme.divider, width: 2)
              : null,
        ),
        alignment: Alignment.center,
        child: loading
            ? const SizedBox(
                width: 22,
                height: 22,
                child: CircularProgressIndicator(
                    strokeWidth: 2.4, color: PosTheme.accent),
              )
            : Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  if (icon != null) ...[
                    Icon(icon, size: 20, color: fg),
                    const SizedBox(width: 8),
                  ],
                  Text(
                    label,
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      color: fg,
                    ),
                  ),
                ],
              ),
      ),
    );
  }
}
