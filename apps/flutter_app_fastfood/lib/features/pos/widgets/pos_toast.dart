// features/pos/widgets/pos_toast.dart
//
// Centered bottom pill toast driven by PosState.toast.
//
// Placement: outermost layer of the PosScreen Stack so it floats above
// the cart overlay and all other content.
//
// Auto-dismiss: an internal timer fires PosNotifier.clearToast after
// _kDisplayDuration. AnimatedSwitcher provides fade + slide transitions.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../pos_state.dart';
import '../pos_theme.dart';

/// How long the toast remains visible before auto-dismissing.
const Duration _kDisplayDuration = Duration(seconds: 2);

/// Centered bottom pill toast.
///
/// Reads [PosState.toast] — when non-null the pill slides up and fades in.
/// After [_kDisplayDuration] it calls [PosNotifier.clearToast] which triggers
/// the fade-out via [AnimatedSwitcher].
class PosToast extends ConsumerWidget {
  const PosToast({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final message = ref.watch(
      posNotifierProvider.select((s) => s.toast),
    );

    return Positioned(
      bottom: 32,
      left: 0,
      right: 0,
      child: AnimatedSwitcher(
        duration: const Duration(milliseconds: 220),
        transitionBuilder: (child, animation) => FadeTransition(
          opacity: animation,
          child: SlideTransition(
            // Slides up from slightly below on enter, slides back down on exit.
            position: Tween<Offset>(
              begin: const Offset(0, 0.4),
              end: Offset.zero,
            ).animate(CurvedAnimation(
              parent: animation,
              curve: Curves.easeOut,
            )),
            child: child,
          ),
        ),
        child: message != null
            ? _ToastPill(key: ValueKey(message), message: message)
            : const SizedBox.shrink(key: ValueKey('hidden')),
      ),
    );
  }
}

/// The visible pill. Schedules auto-dismiss via [Future.delayed] in [initState].
class _ToastPill extends ConsumerStatefulWidget {
  final String message;
  const _ToastPill({required this.message, super.key});

  @override
  ConsumerState<_ToastPill> createState() => _ToastPillState();
}

class _ToastPillState extends ConsumerState<_ToastPill> {
  @override
  void initState() {
    super.initState();
    // Auto-clear after the display window expires.
    Future.delayed(_kDisplayDuration, () {
      if (mounted) ref.read(posNotifierProvider.notifier).clearToast();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
        decoration: const BoxDecoration(
          color: PosTheme.neutral900,
          borderRadius: PosTheme.pillRadius,
          boxShadow: PosTheme.shadowLg,
        ),
        child: Text(
          widget.message,
          style: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w500,
            color: Colors.white,
          ),
        ),
      ),
    );
  }
}
