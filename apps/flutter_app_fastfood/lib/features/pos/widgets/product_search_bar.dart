// features/pos/widgets/product_search_bar.dart
//
// Free-text product search box for the POS catalog — filters by product
// name, product code, or an attached Variant Selection group/option name
// (e.g. typing "16GB" or "Colors" finds every product offering it), across
// every category. Debounced so typing doesn't fire a DB query per keystroke.

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../pos_state.dart';
import '../pos_theme.dart';

class ProductSearchBar extends ConsumerStatefulWidget {
  const ProductSearchBar({super.key});

  @override
  ConsumerState<ProductSearchBar> createState() => _ProductSearchBarState();
}

class _ProductSearchBarState extends ConsumerState<ProductSearchBar> {
  final _controller = TextEditingController();
  Timer? _debounce;

  @override
  void dispose() {
    _debounce?.cancel();
    _controller.dispose();
    super.dispose();
  }

  void _onChanged(String value) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 250), () {
      ref.read(posNotifierProvider.notifier).setSearchQuery(value);
    });
  }

  /// Enter / the keyboard's search action: apply immediately (no debounce
  /// wait) and dismiss the keyboard — the cashier asked for the filter, not
  /// to keep typing.
  void _onSubmitted(String value) {
    _debounce?.cancel();
    ref.read(posNotifierProvider.notifier).setSearchQuery(value);
    FocusScope.of(context).unfocus();
  }

  void _clear() {
    _debounce?.cancel();
    _controller.clear();
    ref.read(posNotifierProvider.notifier).setSearchQuery('');
    FocusScope.of(context).unfocus();
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 44,
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: PosTheme.pillRadius,
        boxShadow: PosTheme.shadowSm,
      ),
      child: TextField(
        controller: _controller,
        onChanged: (v) {
          _onChanged(v);
          setState(() {}); // refresh the clear button's visibility
        },
        textInputAction: TextInputAction.search,
        onSubmitted: _onSubmitted,
        style: const TextStyle(fontSize: 14, color: PosTheme.text),
        decoration: InputDecoration(
          isDense: true,
          hintText: 'Search products, specs, or variants…',
          hintStyle: const TextStyle(fontSize: 14, color: PosTheme.textMuted),
          border: InputBorder.none,
          prefixIcon:
              const Icon(Icons.search, size: 20, color: PosTheme.textMuted),
          suffixIcon: _controller.text.isEmpty
              ? null
              : IconButton(
                  icon: const Icon(Icons.close,
                      size: 18, color: PosTheme.textMuted),
                  onPressed: _clear,
                ),
          contentPadding: const EdgeInsets.symmetric(vertical: 12),
        ),
      ),
    );
  }
}
