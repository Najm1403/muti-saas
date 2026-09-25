// features/shift/shift_open_screen.dart
//
// Opens a new cashier shift: opening cash count + optional note.

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/network/api_exception.dart';
import '../../providers/auth_notifier.dart';
import '../../providers/currency_provider.dart';
import '../../providers/session_notifier.dart';
import '../common/pill_button.dart';
import '../pos/pos_theme.dart';

class ShiftOpenScreen extends ConsumerStatefulWidget {
  const ShiftOpenScreen({super.key});

  @override
  ConsumerState<ShiftOpenScreen> createState() => _ShiftOpenScreenState();
}

class _ShiftOpenScreenState extends ConsumerState<ShiftOpenScreen> {
  final _cash = TextEditingController(text: '0.00');
  final _notes = TextEditingController();
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _cash.dispose();
    _notes.dispose();
    super.dispose();
  }

  Future<void> _open() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await ref.read(sessionNotifierProvider.notifier).openSession(
            openingCash: _cash.text.trim().isEmpty ? '0.00' : _cash.text.trim(),
            notes: _notes.text.trim().isEmpty ? null : _notes.text.trim(),
          );
      if (mounted) context.go('/dashboard');
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) setState(() => _error = 'Could not reach the server');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final currency = ref.watch(currencyProvider);
    final name = ref.watch(authNotifierProvider).valueOrNull?.cashierName ?? '';

    return Scaffold(
      backgroundColor: PosTheme.bg,
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 420),
          child: Padding(
            padding: const EdgeInsets.all(28),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Text('OPEN SHIFT',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.6,
                      color: PosTheme.accentText,
                    )),
                const SizedBox(height: 6),
                Text(
                  name.isEmpty ? 'Start your shift' : 'Welcome, $name',
                  style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w800,
                      color: PosTheme.text),
                ),
                const SizedBox(height: 24),
                const Text('Opening cash in drawer',
                    style: TextStyle(fontSize: 13, color: PosTheme.textMuted)),
                const SizedBox(height: 8),
                TextField(
                  controller: _cash,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  inputFormatters: [
                    FilteringTextInputFormatter.allow(RegExp(r'[0-9.]')),
                  ],
                  style: const TextStyle(
                      fontSize: 22, fontWeight: FontWeight.w700),
                  decoration: InputDecoration(
                    prefixText: '$currency ',
                    filled: true,
                    fillColor: PosTheme.surface,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(16),
                      borderSide: BorderSide.none,
                    ),
                    contentPadding: const EdgeInsets.symmetric(
                        horizontal: 16, vertical: 16),
                  ),
                ),
                const SizedBox(height: 14),
                TextField(
                  controller: _notes,
                  decoration: InputDecoration(
                    hintText: 'Note (optional)',
                    filled: true,
                    fillColor: PosTheme.surface,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(16),
                      borderSide: BorderSide.none,
                    ),
                    contentPadding: const EdgeInsets.symmetric(
                        horizontal: 16, vertical: 14),
                  ),
                ),
                if (_error != null) ...[
                  const SizedBox(height: 10),
                  Text(_error!,
                      style: const TextStyle(
                          color: Color(0xFFD84315), fontSize: 13)),
                ],
                const SizedBox(height: 20),
                PillButton(
                  label: 'Open shift',
                  loading: _loading,
                  onTap: _open,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
