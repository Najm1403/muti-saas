// features/activation/device_locked_screen.dart
//
// Full-screen block shown when the server reports this device as SUSPENDED.
// (A REVOKED device is wiped and sent back to the activation screen instead.)

import 'package:flutter/material.dart';

import '../pos/pos_theme.dart';
import '../common/pill_button.dart';

class DeviceLockedScreen extends StatelessWidget {
  /// Called when the user taps "Retry" — clears the lock so the next API call
  /// re-checks the device status.
  final VoidCallback onRetry;

  const DeviceLockedScreen({super.key, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: PosTheme.bg,
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 420),
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Center(
                  child: Container(
                    width: 84,
                    height: 84,
                    decoration: const BoxDecoration(
                      color: PosTheme.accentLight,
                      borderRadius: PosTheme.pillRadius,
                    ),
                    child: const Icon(Icons.lock_outline,
                        color: PosTheme.accentDark, size: 40),
                  ),
                ),
                const SizedBox(height: 24),
                const Text(
                  'Device suspended',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.w800,
                    color: PosTheme.text,
                  ),
                ),
                const SizedBox(height: 10),
                const Text(
                  'This POS has been suspended. Ask your manager to reactivate '
                  'it from the dashboard, then try again.',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 13, color: PosTheme.textMuted),
                ),
                const SizedBox(height: 28),
                PillButton(label: 'Retry', onTap: onRetry),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
