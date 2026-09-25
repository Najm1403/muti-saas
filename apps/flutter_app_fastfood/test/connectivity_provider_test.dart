import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fastfood_pos/providers/connectivity_provider.dart';

void main() {
  test('loopback API is usable without a public network interface', () {
    expect(
      hasApiConnectivity(
        const [ConnectivityResult.none],
        apiUrl: 'http://127.0.0.1:8000',
      ),
      isTrue,
    );
    expect(
      hasApiConnectivity(
        const [ConnectivityResult.none],
        apiUrl: 'http://localhost:8000',
      ),
      isTrue,
    );
  });

  test('remote API follows device connectivity', () {
    expect(
      hasApiConnectivity(
        const [ConnectivityResult.none],
        apiUrl: 'https://shop.example.com',
      ),
      isFalse,
    );
    expect(
      hasApiConnectivity(
        const [ConnectivityResult.wifi],
        apiUrl: 'https://shop.example.com',
      ),
      isTrue,
    );
  });
}
