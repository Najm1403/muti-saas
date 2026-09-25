import 'package:flutter/material.dart';

import '../../common/pill_button.dart';
import '../../pos/pos_theme.dart';

/// Credentials collected from the admin authorisation sheet.
typedef AdminCreds = ({String username, String pin});

/// Shows a bottom sheet asking an admin for their username + PIN.
///
/// Returns the entered credentials, or null if dismissed. Verification happens
/// server-side (register-device / re-validate accept PIN or password).
Future<AdminCreds?> showAdminPinSheet(
  BuildContext context, {
  String title = 'Admin authorisation',
  String subtitle = 'A manager must approve this action.',
}) {
  return showModalBottomSheet<AdminCreds>(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.white,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
    ),
    builder: (ctx) => _AdminPinSheet(title: title, subtitle: subtitle),
  );
}

class _AdminPinSheet extends StatefulWidget {
  final String title;
  final String subtitle;
  const _AdminPinSheet({required this.title, required this.subtitle});

  @override
  State<_AdminPinSheet> createState() => _AdminPinSheetState();
}

class _AdminPinSheetState extends State<_AdminPinSheet> {
  final _user = TextEditingController();
  final _pin = TextEditingController();
  String? _error;

  @override
  void dispose() {
    _user.dispose();
    _pin.dispose();
    super.dispose();
  }

  void _confirm() {
    final u = _user.text.trim();
    final p = _pin.text.trim();
    if (u.isEmpty || p.length < 4) {
      setState(() => _error = 'Enter the admin username and a 4-6 digit PIN');
      return;
    }
    Navigator.of(context).pop((username: u, pin: p));
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.fromLTRB(
        24,
        20,
        24,
        24 + MediaQuery.of(context).viewInsets.bottom,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Center(
            child: Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: PosTheme.divider,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 18),
          Text(widget.title,
              style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w800,
                  color: PosTheme.text)),
          const SizedBox(height: 4),
          Text(widget.subtitle,
              style: const TextStyle(fontSize: 13, color: PosTheme.textMuted)),
          const SizedBox(height: 18),
          TextField(
            controller: _user,
            decoration: _dec('Admin username'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _pin,
            keyboardType: TextInputType.number,
            obscureText: true,
            maxLength: 6,
            onSubmitted: (_) => _confirm(),
            decoration: _dec('PIN or password').copyWith(
              counterText: '',
              errorText: _error,
            ),
          ),
          const SizedBox(height: 16),
          PillButton(label: 'Authorise', onTap: _confirm),
        ],
      ),
    );
  }

  InputDecoration _dec(String hint) => InputDecoration(
        hintText: hint,
        filled: true,
        fillColor: PosTheme.surface,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide.none,
        ),
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
      );
}
