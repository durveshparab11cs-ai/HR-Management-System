import 'package:geolocator/geolocator.dart';

/// Mock location service for testing GPS functionality
class MockLocationService {
  Position? _mockPosition;
  LocationPermission? _mockPermission;

  /// Set mock position
  void setMockPosition({
    required double latitude,
    required double longitude,
    double accuracy = 5.0,
  }) {
    _mockPosition = Position(
      latitude: latitude,
      longitude: longitude,
      timestamp: DateTime.now(),
      accuracy: accuracy,
      altitude: 0,
      heading: 0,
      speed: 0,
      speedAccuracy: 0,
      altitudeAccuracy: 0,
      headingAccuracy: 0,
    );
  }

  /// Set mock permission
  void setMockPermission(LocationPermission permission) {
    _mockPermission = permission;
  }

  Future<LocationPermission> checkPermission() async {
    return _mockPermission ?? LocationPermission.deniedForever;
  }

  Future<LocationPermission> requestPermission() async {
    return _mockPermission ?? LocationPermission.whileInUse;
  }

  Future<Position> getCurrentPosition({
    LocationAccuracy desiredAccuracy = LocationAccuracy.best,
    bool forceAndroidLocationManager = false,
    Duration timeLimit = const Duration(seconds: 10),
  }) async {
    if (_mockPosition == null) {
      throw Exception('Mock position not set');
    }
    return _mockPosition!;
  }

  Future<bool> isLocationServiceEnabled() async {
    return _mockPosition != null;
  }
}
