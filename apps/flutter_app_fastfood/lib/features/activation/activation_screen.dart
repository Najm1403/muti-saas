// features/activation/activation_screen.dart
//
// The entire first-install experience: enter the 4-digit activation code the
// tenant generated in the web dashboard. The server already knows the
// restaurant / branch / device type from the code.

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/network/api_exception.dart';
import '../../providers/onboarding_notifier.dart';
import '../common/pill_button.dart';
import '../pos/pos_theme.dart';

class ActivationScreen extends ConsumerStatefulWidget {
  const ActivationScreen({super.key});

  @override
  ConsumerState<ActivationScreen> createState() => _ActivationScreenState();
}

class _ActivationScreenState extends ConsumerState<ActivationScreen> {
  final _controller = TextEditingController();
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  String get _digits => _controller.text.replaceAll(RegExp(r'\D'), '');

  Future<void> _submit() async {
    if (_digits.length != 4) {
      setState(() => _error = 'Enter the 4-digit activation code');
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await ref.read(onboardingNotifierProvider.notifier).activate(_digits);
      if (mounted) context.go('/staff');
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
                  child: Image.asset(
                    'assets/smartshop.png',
                    width: 108,
                    height: 108,
                    fit: BoxFit.contain,
                    semanticLabel: 'Storixx logo',
                  ),
                ),
                const SizedBox(height: 24),
                const Text(
                  'STORIXX',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w800,
                    color: PosTheme.text,
                  ),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Activate this POS',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 14, color: PosTheme.textMuted),
                ),
                const SizedBox(height: 36),
                const Text(
                  'ACTIVATION CODE',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.6,
                    color: PosTheme.accentText,
                  ),
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: _controller,
                  autofocus: true,
                  keyboardType: TextInputType.number,
                  textAlign: TextAlign.center,
                  maxLength: 5, // 4 digits + optional space
                  onSubmitted: (_) => _submit(),
                  onChanged: (_) {
                    if (_error != null) setState(() => _error = null);
                  },
                  inputFormatters: [
                    FilteringTextInputFormatter.allow(RegExp(r'[0-9 ]')),
                  ],
                  style: const TextStyle(
                    fontSize: 30,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 8,
                    color: PosTheme.text,
                  ),
                  decoration: InputDecoration(
                    counterText: '',
                    hintText: '58 32',
                    hintStyle: const TextStyle(
                      color: PosTheme.textMuted,
                      letterSpacing: 8,
                      fontWeight: FontWeight.w600,
                    ),
                    filled: true,
                    fillColor: PosTheme.surface,
                    errorText: _error,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(16),
                      borderSide: BorderSide.none,
                    ),
                    contentPadding: const EdgeInsets.symmetric(
                        horizontal: 16, vertical: 18),
                  ),
                ),
                const SizedBox(height: 20),
                PillButton(
                  label: 'Activate',
                  loading: _loading,
                  onTap: _submit,
                ),
                const SizedBox(height: 12),
                const Text(
                  'Connection to your shop server is required.\n'
                  'Your manager creates this code in the web dashboard.',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 12, color: PosTheme.textMuted),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
