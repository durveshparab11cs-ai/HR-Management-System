# Phase 3 Quick Start Guide

## ✅ What's Ready

All Phase 3 enhancements have been **integrated and implemented**:
- ✓ Image compression service
- ✓ Permission management
- ✓ Offline attendance queue
- ✓ Connectivity monitoring
- ✓ Background sync with workmanager
- ✓ Biometric authentication
- ✓ All screens updated
- ✓ Native permissions configured (Android + iOS)

---

## 🚀 Getting Started

### 1. Prerequisites
```bash
# Ensure you have Flutter installed
flutter --version

# Should output something like:
# Flutter 3.19.0 • channel stable
# Dart 3.3.0
```

### 2. Install Dependencies
```bash
cd "c:\Users\durve\Downloads\HR management system\smart_hrms_mobile"
flutter pub get
```

### 3. Update .env File
```bash
# Edit .env with your backend API URL
BACKEND_URL=http://your-backend-url:5000
JWT_SECRET=your-secret-key
```

### 4. Run the App
```bash
# On Android emulator/device
flutter run -d emulator_name

# On iOS simulator/device  
flutter run -d iphone

# Build APK for testing
flutter build apk --release

# Build IPA for iOS testing
flutter build ios --release
```

---

## 🧪 Testing Phase 3 Features

### Test 1: Image Compression
```
1. Open app → Check-In screen
2. Tap "Capture Photo"
3. Take a large photo (>2MB)
4. Check console logs for:
   "Image compressed: 2000KB → 450KB at quality 75%"
5. Photo should upload successfully
```

### Test 2: Permissions
```
1. First app launch → Watch permission dialogs
2. Should request: Location + Camera
3. Grant all permissions
4. Check Settings: All permissions should show as granted
```

### Test 3: Offline Mode
```
1. Turn off device WiFi + mobile data
2. Try check-in → Should fail or queue
3. Check settings → Manual Sync shows "No internet"
4. Turn internet back on
5. Manual Sync starts automatically
6. Check logs for successful sync
```

### Test 4: Biometric Login
```
1. Login manually once with credentials
2. Toggle "Remember me" (for secure storage)
3. Log out
4. On login screen → "Use Biometric" button visible
5. Tap biometric button
6. Authenticate with fingerprint/face
7. Should login automatically
```

### Test 5: Connectivity Indicator
```
1. Open Check-In screen
2. Turn off internet → Offline indicator shows
3. Turn on internet → Offline indicator disappears
4. Manual sync button should work when online
```

---

## 📱 Device Requirements

### Android
- Minimum SDK: Android 8 (API 26)
- Camera: Required for selfies
- GPS: Required for location
- Biometric: Optional (Fingerprint/Face ID)

### iOS  
- Minimum iOS: 12.0
- Camera: Required
- Location: Required
- Face ID: Optional (on supported devices)
- Touch ID: Optional (on supported devices)

---

## 🔍 Debugging

### View Logs
```bash
# Real-time logs
flutter logs

# Filter by app
flutter logs | grep "smart_hrms"

# Search for specific tag
flutter logs | grep "ImageCompression"
```

### Enable Debug Logging
In `main.dart`, change to:
```dart
await Workmanager().initialize(
  callbackDispatcher,
  isInDebugMode: true,  // ← Set to true for debug logs
);
```

### Common Issues

**Issue**: "Permission denied" on check-in
```
Solution: Grant location + camera permissions in settings
```

**Issue**: Biometric button not showing
```
Solution: Device doesn't support biometric or not enrolled
- Check Settings → Biometric Settings
- Ensure fingerprint/face ID is set up on device
```

**Issue**: "No internet" during sync
```
Solution: Check device connectivity
- Turn WiFi off → on
- Check mobile data
- Verify backend URL in .env
```

**Issue**: Photo not uploading
```
Solution: Image compression issue
- Check image size before compression
- Verify storage permissions
- Check backend endpoint: POST /api/v1/attendance/upload-photo
```

---

## 📋 Phase 3 Services Overview

### Service Locations
```
lib/core/services/
├── image_compression_service.dart       - Photo compression
├── permission_service.dart               - Permission handling  
├── connectivity_service.dart             - Network monitoring
├── sync_service.dart                     - Offline queue sync
├── biometric_service.dart                - Fingerprint/Face ID
└── services_providers.dart               - Riverpod exports
```

### Widget Locations
```
lib/core/widgets/
└── offline_indicator_widget.dart         - Offline UI indicators
```

### Screen Integrations
```
lib/features/
├── attendance/screens/check_in_screen.dart
│   ├── Uses: image_compression, permission, connectivity
│   └── Shows: offline indicator, pending records
├── auth/screens/login_screen.dart
│   ├── Uses: biometric service
│   └── Shows: Use Biometric button
└── settings/screens/
    ├── settings_screen.dart
    │   ├── Shows: biometric toggle, manual sync
    │   └── Uses: sync service
    └── biometric_settings_screen.dart
        ├── Shows: available biometric types
        └── Uses: biometric service
```

---

## 🔐 Security Checklist

- [x] Secure token storage (flutter_secure_storage)
- [x] HTTPS only (production)
- [x] JWT token refresh on 401
- [x] Permission checks before API calls
- [x] Input validation on forms
- [x] Biometric + password authentication
- [x] Offline queue timeout (48 hours)
- [x] Automatic retry with backoff

---

## 📊 Performance Tips

### Image Compression
- Target size: <500KB
- Quality range: 50-85%
- Reduces upload time by 70-80%

### Offline Queue
- Max retries: 3
- TTL: 48 hours
- Auto-sync on connectivity restore

### Background Sync
- Scheduled every 15 minutes
- Only runs when battery >20%
- Uses exponential backoff

### Network
- Connection timeout: 30 seconds
- Read timeout: 30 seconds
- Auto-retry on timeout (max 2 times)

---

## 🛠️ Development Tips

### Add New Feature using Phase 3
```dart
// 1. Inject service in provider
final newFeatureProvider = FutureProvider((ref) async {
  final permissionService = ref.read(permissionServiceProvider);
  
  // 2. Check permissions
  if (!await permissionService.requestLocationPermission()) {
    throw 'Permission denied';
  }
  
  // 3. Call API
  return apiCall();
});

// 4. Watch in widget
final data = ref.watch(newFeatureProvider);
```

### Monitor Network Status
```dart
final networkStatus = ref.watch(networkStatusProvider);

networkStatus.when(
  data: (status) {
    if (status.isOffline) {
      // Handle offline
    }
  },
  loading: () => CircularProgressIndicator(),
  error: (err, st) => ErrorWidget(),
);
```

### Manual Sync Trigger
```dart
final syncService = ref.read(syncServiceProvider);
final result = await syncService.syncPendingAttendance();

print('Synced ${result.syncedCount} records');
print('${result.failedCount} failed');
```

---

## 📞 Support

For issues or questions:
1. Check logs with `flutter logs`
2. Review Phase 3 implementation guide: `PHASE3_IMPLEMENTATION_GUIDE.md`
3. Check integration status: `PHASE3_INTEGRATION_COMPLETED.md`
4. Review original planning: `PHASE3_ENHANCEMENTS.md`

---

## ✅ Next: Build & Deploy

### Android Build
```bash
# Debug
flutter build apk

# Release (production)
flutter build apk --release

# Output: build/app/outputs/flutter-apk/app-release.apk
```

### iOS Build
```bash
# Debug
flutter build ios

# Release
flutter build ios --release

# Output: build/ios/iphoneos/Runner.app
```

### Deploy to Stores
```bash
# Android Play Store
flutter build appbundle --release
# Upload to Play Console

# iOS App Store  
flutter build ios --release
# Archive and upload via Xcode
```

---

**Ready to test Phase 3!** 🚀

