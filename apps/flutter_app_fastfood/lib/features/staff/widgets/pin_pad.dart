import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../pos/pos_theme.dart';

/// Shows a modal numeric PIN pad for [staffName].
///
/// Returns the entered PIN (4-6 digits) when the user confirms, or null on
/// cancel. Verification is done by the caller against the server.
Future<String?> showPinPad(BuildContext context, {required String staffName}) {
  return showDialog<String>(
    context: context,
    barrierDismissible: true,
    builder: (_) => _PinPadDialog(staffName: staffName),
  );
}

class _PinPadDialog extends StatefulWidget {
  final String staffName;
  const _PinPadDialog({required this.staffName});

  @override
  State<_PinPadDialog> createState() => _PinPadDialogState();
}

class _PinPadDialogState extends State<_PinPadDialog> {
  static const _max = 6;
  static const _min = 4;
  String _pin = '';
  bool _busy = false;
  String? _error;

  // Physical-keyboard support (desktop / attached keyboards).
  final FocusNode _focus = FocusNode();

  @override
  void dispose() {
    _focus.dispose();
    super.dispose();
  }

  void _onKeyEvent(KeyEvent event) {
    if (event is! KeyDownEvent || _busy) return;
    final k = event.logicalKey;
    if (k == LogicalKeyboardKey.backspace) {
      _back();
    } else if (k == LogicalKeyboardKey.enter ||
        k == LogicalKeyboardKey.numpadEnter) {
      _confirm();
    } else {
      final ch = event.character;
      if (ch != null && ch.length == 1 && '0123456789'.contains(ch)) {
        _tap(ch);
      }
    }
  }

  void _tap(String d) {
    if (_pin.length >= _max) return;
    setState(() {
      _pin += d;
      _error = null;
    });
  }

  void _back() {
    if (_pin.isEmpty) return;
    setState(() => _pin = _pin.substring(0, _pin.length - 1));
  }

  void _confirm() {
    if (_pin.length < _min) {
      setState(() => _error = 'Enter at least $_min digits');
      return;
    }
    setState(() => _busy = true);
    Navigator.of(context).pop(_pin);
  }

  @override
  Widget build(BuildContext context) {
    return KeyboardListener(
      focusNode: _focus,
      autofocus: true,
      onKeyEvent: _onKeyEvent,
      child: Dialog(
      backgroundColor: Colors.white,
      shape:
          RoundedRectangleBorder(borderRadius: BorderRadius.circular(28)),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(24, 24, 24, 20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              widget.staffName,
              style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w800,
                  color: PosTheme.text),
            ),
            const SizedBox(height: 4),
            const Text('Enter your PIN',
                style: TextStyle(fontSize: 13, color: PosTheme.textMuted)),
            const SizedBox(height: 20),
            // Dots.
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(_max, (i) {
                final filled = i < _pin.length;
                return Container(
                  width: 14,
                  height: 14,
                  margin: const EdgeInsets.symmetric(horizontal: 6),
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: filled ? PosTheme.accent : PosTheme.neutral200,
                  ),
                );
              }),
            ),
            if (_error != null) ...[
              const SizedBox(height: 10),
              Text(_error!,
                  style: const TextStyle(
                      fontSize: 12, color: Color(0xFFD84315))),
            ],
            const SizedBox(height: 18),
            // Keypad.
            for (final row in const [
              ['1', '2', '3'],
              ['4', '5', '6'],
              ['7', '8', '9'],
              ['', '0', 'back'],
            ])
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  for (final k in row) _Key(label: k, onTap: _onKey),
                ],
              ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: GestureDetector(
                onTap: _busy ? null : _confirm,
                child: Container(
                  height: 50,
                  decoration: BoxDecoration(
                    color: _busy ? PosTheme.neutral200 : PosTheme.accent,
                    borderRadius: PosTheme.pillRadius,
                  ),
                  alignment: Alignment.center,
                  child: _busy
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                              strokeWidth: 2.2, color: PosTheme.accent))
                      : const Text('Sign in',
                          style: TextStyle(
                              fontSize: 15,
                              fontWeight: FontWeight.w700,
                              color: Colors.white)),
                ),
              ),
            ),
          ],
        ),
      ),
      ),
    );
  }

  void _onKey(String k) {
    if (k == 'back') {
      _back();
    } else if (k.isNotEmpty) {
      _tap(k);
    }
  }
}

class _Key extends StatelessWidget {
  final String label;
  final ValueChanged<String> onTap;
  const _Key({required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    if (label.isEmpty) {
      return const SizedBox(width: 68, height: 60);
    }
    return GestureDetector(
      onTap: () => onTap(label),
      child: Container(
        width: 68,
        height: 60,
        margin: const EdgeInsets.all(4),
        decoration: BoxDecoration(
          color: PosTheme.surface,
          borderRadius: BorderRadius.circular(18),
        ),
        alignment: Alignment.center,
        child: label == 'back'
            ? const Icon(Icons.backspace_outlined,
                size: 22, color: PosTheme.text)
            : Text(label,
                style: const TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w700,
                    color: PosTheme.text)),
      ),
    );
  }
}
