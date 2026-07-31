import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:mockito/mockito.dart';

/// Mock connectivity service for testing network availability
class MockConnectivityService extends Mock implements Connectivity {
  bool _isOnline = true;

  /// Set online/offline state
  void setOnline(bool online) {
    _isOnline = online;
  }

  /// Get current online state
  bool get isOnline => _isOnline;

  @override
  Future<List<ConnectivityResult>> checkConnectivity() async {
    if (_isOnline) {
      return [ConnectivityResult.mobile];
    }
    return [ConnectivityResult.none];
  }

  @override
  Stream<List<ConnectivityResult>> get onConnectivityChanged {
    if (_isOnline) {
      return Stream.value([ConnectivityResult.mobile]);
    }
    return Stream.value([ConnectivityResult.none]);
  }
}
