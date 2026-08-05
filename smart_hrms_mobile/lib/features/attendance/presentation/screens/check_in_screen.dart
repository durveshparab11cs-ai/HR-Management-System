import 'dart:io';
import 'dart:math';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/services/connectivity_service.dart';
import '../../../../core/services/permission_service.dart';
import '../../../../core/services/services_providers.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/offline_indicator_widget.dart';
import '../providers/attendance_provider.dart';

class CheckInScreen extends ConsumerStatefulWidget {
  const CheckInScreen({super.key});

  @override
  ConsumerState<CheckInScreen> createState() => _CheckInScreenState();
}

class _CheckInScreenState extends ConsumerState<CheckInScreen> {
  CameraController? _cameraController;
  bool _isCameraInitialized = false;
  bool _isLoadingLocation = false;
  Position? _currentPosition;
  String? _capturedImagePath;
  bool _isCheckOut = false;
  bool _locationValidated = false;
  double? _verifiedDistance;

  @override
  void initState() {
    super.initState();
    _checkAttendanceStatus();
    // Don't initialize camera yet - wait for location validation
  }

  Future<void> _checkAttendanceStatus() async {
    final todayAttendance = await ref.read(todayAttendanceProvider.future);
    setState(() {
      _isCheckOut = todayAttendance.hasCheckedIn && !todayAttendance.hasCheckedOut;
    });
  }

  Future<void> _initializeCamera() async {
    try {
      final cameras = await availableCameras();
      if (cameras.isEmpty) {
        _showError('No camera available on this device');
        return;
      }

      final frontCamera = cameras.firstWhere(
        (camera) => camera.lensDirection == CameraLensDirection.front,
        orElse: () => cameras.first,
      );

      _cameraController = CameraController(
        frontCamera,
        ResolutionPreset.medium,
        enableAudio: false,
      );

      await _cameraController!.initialize();
      if (mounted) {
        setState(() => _isCameraInitialized = true);
      }
    } catch (e) {
      _showError('Failed to initialize camera: $e');
    }
  }

  Future<void> _getCurrentLocation() async {
    setState(() => _isLoadingLocation = true);

    try {
      // Request permission using Phase 3 PermissionService
      final hasPermission = await PermissionService.requestLocationPermission();

      if (!hasPermission) {
        throw 'Location permissions denied';
      }

      // iOS SPECIFIC FIX: Get multiple location samples and use the most accurate
      // iOS GPS can have high variance on first fix, so we wait for multiple readings
      final List<Position> positions = [];
      final startTime = DateTime.now();
      const maxWaitTime = Duration(seconds: 15);
      const minAccuracy = 30.0; // meters - good GPS accuracy threshold

      debugPrint('[GPS] Starting iOS multi-sample GPS collection...');

      // Collect multiple GPS samples
      final locationStream = Geolocator.getPositionStream(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.best,
          distanceFilter: 0, // Get every update
          timeLimit: maxWaitTime,
        ),
      );

      await for (final position in locationStream) {
        positions.add(position);
        debugPrint(
          '[GPS] Sample ${positions.length}: lat=${position.latitude}, '
          'lon=${position.longitude}, accuracy=${position.accuracy}m',
        );

        // Stop if we get good accuracy or timeout
        if (position.accuracy <= minAccuracy ||
            DateTime.now().difference(startTime) > maxWaitTime) {
          debugPrint(
            '[GPS] Stopping collection - accuracy=${position.accuracy}m, '
            'samples=${positions.length}',
          );
          break;
        }

        // Also stop if we have enough samples with decent accuracy
        if (positions.length >= 3 &&
            positions.every((p) => p.accuracy <= 50)) {
          debugPrint(
            '[GPS] Stopping collection - enough good samples, '
            'accuracy=${position.accuracy}m',
          );
          break;
        }

        // Safety: hard stop at 30 samples
        if (positions.length >= 30) {
          debugPrint('[GPS] Reached max samples, stopping collection');
          break;
        }
      }

      if (positions.isEmpty) {
        throw 'Unable to get GPS location. Please enable location services.';
      }

      // Use the position with best (lowest) accuracy
      final bestPosition = positions.reduce((a, b) =>
          a.accuracy < b.accuracy ? a : b);

      debugPrint(
        '[GPS] Selected best position: accuracy=${bestPosition.accuracy}m, '
        'samples collected=${positions.length}',
      );

      setState(() {
        _currentPosition = bestPosition;
        _isLoadingLocation = false;
      });

      // Validate location with office settings
      await _validateLocation(bestPosition);
    } catch (e) {
      setState(() => _isLoadingLocation = false);
      _showError('Location error: $e');
    }
  }

  Future<void> _validateLocation(Position position) async {
    try {
      final officeSettings = await ref.read(officeSettingsProvider.future);
      
      final distance = _calculateDistance(
        position.latitude,
        position.longitude,
        officeSettings.latitude,
        officeSettings.longitude,
      );

      if (distance > officeSettings.radiusMeters) {
        _showError(
          'You are ${distance.toInt()}m away from office. '
          'Required distance: ${officeSettings.radiusMeters}m. '
          'Cannot proceed with check-in.',
        );
        setState(() {
          _locationValidated = false;
          _verifiedDistance = null;
        });
      } else {
        // Location is valid - now initialize camera
        setState(() {
          _locationValidated = true;
          _verifiedDistance = distance;
        });
        _showSuccess(
          'Location verified! You are ${distance.toInt()}m from office. '
          'Camera is ready.',
        );
        
        // Initialize camera only after location is validated
        await _initializeCamera();
      }
    } catch (e) {
      _showError('Failed to verify location: $e');
      setState(() {
        _locationValidated = false;
        _verifiedDistance = null;
      });
    }
  }

  double _calculateDistance(double lat1, double lon1, double lat2, double lon2) {
    const double earthRadius = 6371000; // meters
    final dLat = _toRadians(lat2 - lat1);
    final dLon = _toRadians(lon2 - lon1);

    final a = sin(dLat / 2) * sin(dLat / 2) +
        cos(_toRadians(lat1)) *
            cos(_toRadians(lat2)) *
            sin(dLon / 2) *
            sin(dLon / 2);

    final c = 2 * atan2(sqrt(a), sqrt(1 - a));
    return earthRadius * c;
  }

  double _toRadians(double degrees) => degrees * pi / 180;

  Future<void> _capturePhoto() async {
    if (_cameraController == null || !_cameraController!.value.isInitialized) {
      _showError('Camera not initialized');
      return;
    }

    try {
      final image = await _cameraController!.takePicture();
      setState(() => _capturedImagePath = image.path);
      _showSuccess('Photo captured successfully');
    } catch (e) {
      _showError('Failed to capture photo: $e');
    }
  }

  Future<void> _handleSubmit() async {
    if (!_locationValidated) {
      _showError('Location not validated. Please verify your location first.');
      return;
    }

    if (_currentPosition == null) {
      _showError('Please get your location first');
      return;
    }

    if (_capturedImagePath == null) {
      _showError('Please capture your photo first');
      return;
    }

    final success = _isCheckOut
        ? await ref.read(checkInOutProvider.notifier).checkOut(
              latitude: _currentPosition!.latitude,
              longitude: _currentPosition!.longitude,
              photoPath: _capturedImagePath,
            )
        : await ref.read(checkInOutProvider.notifier).checkIn(
              latitude: _currentPosition!.latitude,
              longitude: _currentPosition!.longitude,
              photoPath: _capturedImagePath,
            );

    if (!mounted) return;

    if (success) {
      final message = ref.read(checkInOutProvider).successMessage;
      _showSuccess(message ?? 'Check-in successful!');
      
      // Navigate back after delay
      Future.delayed(const Duration(seconds: 2), () {
        if (mounted) context.pop();
      });
    } else {
      final error = ref.read(checkInOutProvider).error ?? 'Operation failed';
      _showError(error);
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: AppTheme.error,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  void _showSuccess(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: AppTheme.success,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  @override
  void dispose() {
    _cameraController?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final checkInOutState = ref.watch(checkInOutProvider);
    final networkStatus = ref.watch(networkStatusProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(_isCheckOut ? 'Check Out' : 'Check In'),
      ),
      body: Stack(
        children: [
          SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Network Status Indicator
                networkStatus.when(
                  data: (status) {
                    if (status.isOffline) {
                      return Padding(
                        padding: const EdgeInsets.only(bottom: 16),
                        child: OfflineIndicatorWidget(),
                      );
                    }
                    return const SizedBox.shrink();
                  },
                  loading: () => const SizedBox.shrink(),
                  error: (_, __) => const SizedBox.shrink(),
                ),

                // Instructions
                Card(
                  color: AppTheme.primary.withOpacity(0.1),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(
                              Icons.info_outline,
                              color: AppTheme.primary,
                              size: 20,
                            ),
                            const SizedBox(width: 8),
                            Text(
                              'Instructions',
                              style: TextStyle(
                                fontSize: 14,
                                fontWeight: FontWeight.w600,
                                color: AppTheme.primary,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text(
                          '1. Tap "Get Location" to verify you\'re in the office\n'
                          '2. Once location is verified, camera will unlock\n'
                          '3. Capture your selfie\n'
                          '4. Submit to ${_isCheckOut ? "check out" : "check in"}',
                          style: const TextStyle(
                            fontSize: 12,
                            color: AppTheme.textSecondary,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 24),

                // Camera Preview
                _buildCameraSection(),

                const SizedBox(height: 24),

                // Location Section
                _buildLocationSection(),

                const SizedBox(height: 32),

                // Submit Button
                FilledButton(
                  onPressed: checkInOutState.isLoading ? null : _handleSubmit,
                  style: FilledButton.styleFrom(
                    minimumSize: const Size.fromHeight(52),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: checkInOutState.isLoading
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            color: Colors.white,
                            strokeWidth: 2,
                          ),
                        )
                      : Text(
                          _isCheckOut ? 'Check Out Now' : 'Check In Now',
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                ),
              ],
            ),
          ),
          // Offline sync status overlay
          networkStatus.when(
            data: (status) {
              if (status.isOffline) {
                return Positioned(
                  bottom: 16,
                  left: 16,
                  right: 16,
                  child: PendingRecordsIndicator(),
                );
              }
              return const SizedBox.shrink();
            },
            loading: () => const SizedBox.shrink(),
            error: (_, __) => const SizedBox.shrink(),
          ),
        ],
      ),
    );
  }

  Widget _buildCameraSection() {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Capture Selfie',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w700,
                color: AppTheme.textPrimary,
              ),
            ),
            const SizedBox(height: 16),
            
            // Show message if location not validated
            if (!_locationValidated)
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppTheme.error.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppTheme.error, width: 1),
                ),
                child: Row(
                  children: [
                    Icon(Icons.lock, color: AppTheme.error, size: 20),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Validate your location first to use camera',
                        style: TextStyle(
                          fontSize: 12,
                          color: AppTheme.error,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                ),
              )
            else ...[
              // Camera preview or captured image
              ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child: AspectRatio(
                  aspectRatio: 3 / 4,
                  child: _capturedImagePath != null
                      ? Image.file(
                          File(_capturedImagePath!),
                          fit: BoxFit.cover,
                        )
                      : _isCameraInitialized
                          ? CameraPreview(_cameraController!)
                          : Container(
                              color: Colors.grey[300],
                              child: const Center(
                                child: CircularProgressIndicator(),
                              ),
                            ),
                ),
              ),

              const SizedBox(height: 16),

              // Capture/Retake button
              if (_capturedImagePath == null)
                FilledButton.icon(
                  onPressed: _isCameraInitialized ? _capturePhoto : null,
                  icon: const Icon(Icons.camera_alt),
                  label: const Text('Capture Photo'),
                  style: FilledButton.styleFrom(
                    minimumSize: const Size.fromHeight(48),
                  ),
                )
              else
                OutlinedButton.icon(
                  onPressed: () => setState(() => _capturedImagePath = null),
                  icon: const Icon(Icons.refresh),
                  label: const Text('Retake Photo'),
                  style: OutlinedButton.styleFrom(
                    minimumSize: const Size.fromHeight(48),
                  ),
                ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildLocationSection() {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Text(
                  'Location',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                    color: AppTheme.textPrimary,
                  ),
                ),
                const SizedBox(width: 8),
                if (_locationValidated)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppTheme.success.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.check_circle, size: 14, color: AppTheme.success),
                        const SizedBox(width: 4),
                        Text(
                          'Verified',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                            color: AppTheme.success,
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 16),

            if (_currentPosition != null) ...[
              _LocationInfo(
                icon: Icons.location_on,
                label: 'Latitude',
                value: _currentPosition!.latitude.toStringAsFixed(6),
              ),
              const SizedBox(height: 12),
              _LocationInfo(
                icon: Icons.location_on,
                label: 'Longitude',
                value: _currentPosition!.longitude.toStringAsFixed(6),
              ),
              const SizedBox(height: 12),
              _LocationInfo(
                icon: Icons.gps_fixed,
                label: 'Accuracy',
                value: '${_currentPosition!.accuracy.toStringAsFixed(1)}m',
              ),
              if (_verifiedDistance != null) ...[
                const SizedBox(height: 12),
                _LocationInfo(
                  icon: Icons.distance_icon,
                  label: 'Distance from Office',
                  value: '${_verifiedDistance!.toInt()}m',
                ),
              ],
              const SizedBox(height: 16),
            ],

            FilledButton.icon(
              onPressed: _isLoadingLocation ? null : _getCurrentLocation,
              icon: _isLoadingLocation
                  ? const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(
                        color: Colors.white,
                        strokeWidth: 2,
                      ),
                    )
                  : const Icon(Icons.my_location),
              label: Text(_locationValidated
                  ? 'Location Verified ✓'
                  : (_currentPosition == null
                      ? 'Get Current Location'
                      : 'Refresh Location')),
              style: FilledButton.styleFrom(
                minimumSize: const Size.fromHeight(48),
                backgroundColor: _locationValidated
                    ? AppTheme.success
                    : (_currentPosition == null
                        ? AppTheme.primary
                        : AppTheme.secondary),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _LocationInfo extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _LocationInfo({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: 20, color: AppTheme.textSecondary),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: const TextStyle(
                  fontSize: 12,
                  color: AppTheme.textSecondary,
                ),
              ),
              Text(
                value,
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: AppTheme.textPrimary,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
