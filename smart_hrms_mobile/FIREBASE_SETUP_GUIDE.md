# Firebase Cloud Messaging Setup Guide

## Overview
This guide explains how to set up Firebase Cloud Messaging (FCM) for the Smart HRMS mobile app to enable push notifications.

---

## Prerequisites
- Firebase project created at [console.firebase.google.com](https://console.firebase.google.com)
- FlutterFire CLI installed: `dart pub global activate flutterfire_cli`
- Android Studio / Xcode installed

---

## Step 1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Click "Create a new project"
3. Enter project name (e.g., "Smart HRMS Mobile")
4. Continue through setup steps
5. Create project

---

## Step 2: Configure Flutter Firebase

### Option A: Using FlutterFire CLI (Recommended)
```bash
cd smart_hrms_mobile
flutterfire configure
```

This will:
- Ask you to select the Firebase project
- Configure Android/iOS automatically
- Generate `lib/firebase_options.dart`

### Option B: Manual Configuration

#### Android Setup
1. Go to Firebase Console → Project Settings → General
2. Scroll to "Your apps" section
3. Click Android app icon
4. Download `google-services.json`
5. Place in: `android/app/google-services.json`

#### iOS Setup
1. Go to Firebase Console → Project Settings → General
2. Scroll to "Your apps" section
3. Click iOS app icon
4. Download `GoogleService-Info.plist`
5. Place in Xcode:
   - Open `ios/Runner.xcworkspace` in Xcode
   - Right-click Runner folder → Add Files
   - Select `GoogleService-Info.plist`
   - Check "Copy items if needed" and "Runner" target

---

## Step 3: Update firebase_options.dart

Replace the placeholder values in `lib/firebase_options.dart` with actual values from Firebase Console:

```dart
// Go to Firebase Console → Project Settings → Your apps
// Copy the values and replace in firebase_options.dart

static const FirebaseOptions android = FirebaseOptions(
  apiKey: 'YOUR_ANDROID_API_KEY',  // From google-services.json
  appId: 'YOUR_ANDROID_APP_ID',
  messagingSenderId: 'YOUR_ANDROID_MESSAGING_SENDER_ID',
  projectId: 'your-firebase-project-id',
  storageBucket: 'your-firebase-project.appspot.com',
);

static const FirebaseOptions ios = FirebaseOptions(
  apiKey: 'YOUR_iOS_API_KEY',
  appId: 'YOUR_iOS_APP_ID',
  messagingSenderId: 'YOUR_iOS_MESSAGING_SENDER_ID',
  projectId: 'your-firebase-project-id',
  storageBucket: 'your-firebase-project.appspot.com',
  iosBundleId: 'com.example.smartHrmsMobile',
);
```

---

## Step 4: Android Configuration

### gradle configuration
In `android/build.gradle`, add Google Services plugin:

```gradle
buildscript {
  dependencies {
    // Add this line
    classpath 'com.google.gms:google-services:4.3.15'
  }
}
```

In `android/app/build.gradle`, apply plugin:

```gradle
apply plugin: 'com.google.gms.google-services'  // Add this line
```

### AndroidManifest.xml
Already configured in `android/app/src/main/AndroidManifest.xml` (from Phase 3)

---

## Step 5: iOS Configuration

### Update Podfile
In `ios/Podfile`, uncomment and set minimum platform version:

```ruby
platform :ios, '11.0'
```

### Run pod install
```bash
cd ios
pod install --repo-update
cd ..
```

---

## Step 6: Backend Integration

### 1. Register FCM Token with Backend
When user logs in, the app registers the FCM token:

```dart
// This happens automatically in main.dart
final notificationService = ref.read(notificationServiceProvider);
final token = await notificationService.getToken();
await notificationActionNotifier.registerFcmToken(token);
```

**Backend Endpoint**: `POST /api/v1/notifications/register-token`
```json
{
  "fcm_token": "device-fcm-token-here"
}
```

### 2. Subscribe to Topics
Users are automatically subscribed to topics:
- `user_<userId>` - Personal notifications
- `role_<role>` - Role-based notifications (manager, admin, etc.)
- `all_users` - General broadcasts

### 3. Send Notifications from Backend
```python
# Example: Send leave approval notification
from firebase_admin import messaging

def send_leave_approval_notification(employee_id, leave_id):
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title='Leave Approved',
            body='Your leave request has been approved',
        ),
        data={
            'type': 'leave_approval',
            'leave_id': str(leave_id),
            'action_url': '/leave/' + str(leave_id),
        },
        topic=f'user_{employee_id}',
    )
    response = messaging.send_multicast(message)
    print(f'{response.success} messages were sent successfully')
```

---

## Step 7: Notification Handling

### Foreground Notifications
When app is open, notifications are handled by:
- `NotificationService.firebaseMessaging.onMessage` listener
- Shows local notification banner
- Emits to `notificationStream`

### Background Notifications
When app is in background or closed:
- Firebase automatically shows notification
- `firebaseMessagingBackgroundHandler` is called
- App stores notification in history

### Notification Tapped
When user taps notification:
- `_handleBackgroundNotification` is triggered
- If `action_url` present, navigates to that route
- Notification marked as read

---

## Step 8: Testing

### Test from Firebase Console

1. Go to Firebase Console → Cloud Messaging
2. Click "Send your first message"
3. Enter notification title and body
4. Select target audience:
   - `User segment` → Create custom rule based on topics
   - Or send to specific device (for testing)
5. Schedule or send immediately

### Test Locally

```dart
// Send test message to specific device
final notificationService = NotificationService();
final token = await notificationService.getToken();
print('Device FCM Token: $token');

// Use this token to send test messages via Firebase Console
```

---

## Step 9: Notification Center Integration

### Add Route
In `lib/core/router/app_router.dart`:

```dart
GoRoute(
  path: '/notifications',
  builder: (context, state) => const NotificationCenterScreen(),
),
```

### Add to Navigation
Update dashboard or settings to link to Notification Center:

```dart
// In any screen
context.push('/notifications');
```

### Add Badge to App Bar
Display unread notification count:

```dart
appBar: AppBar(
  actions: [
    ref.watch(unreadCountProvider).when(
      data: (count) {
        if (count.unreadCount == 0) return SizedBox.shrink();
        return Badge(
          label: Text('${count.unreadCount}'),
          child: Icon(Icons.notifications),
        );
      },
      loading: () => SizedBox.shrink(),
      error: (_, __) => SizedBox.shrink(),
    ),
  ],
),
```

---

## Troubleshooting

### FCM Token is null
**Problem**: `getToken()` returns null
**Solutions**:
1. Ensure Firebase is initialized before calling
2. Check that google-services.json / GoogleService-Info.plist are in correct location
3. Verify API credentials in Firebase Console
4. Try on physical device (not emulator for iOS)

### Notifications Not Arriving
**Problem**: Sent from Firebase Console but device doesn't receive
**Solutions**:
1. Check `flutterfire configure` completed successfully
2. Verify device is subscribed to correct topic
3. Check Android Manifest has correct permissions
4. Enable "Show notification permission" in app settings
5. Check Firebase Console → Cloud Messaging → Delivery Statistics

### Background Handler Not Called
**Problem**: `firebaseMessagingBackgroundHandler` not executing
**Solutions**:
1. Ensure `@pragma('vm:entry-point')` is present
2. Handler must be a top-level function (not a method)
3. Initialize Firebase inside handler: `await Firebase.initializeApp()`
4. Test with real APK/IPA, not debug build

### Xcode Build Fails
**Problem**: Pod-related errors during iOS build
**Solutions**:
```bash
cd ios
rm -rf Podfile.lock
rm -rf Pods
pod install --repo-update
cd ..
flutter clean
flutter pub get
flutter build ios
```

---

## Production Checklist

- [x] Firebase project created and configured
- [x] google-services.json placed in Android
- [x] GoogleService-Info.plist placed in iOS
- [x] firebase_options.dart updated with actual values
- [x] Backend endpoints ready for FCM token registration
- [x] Backend can send notifications via Firebase Admin SDK
- [x] NotificationCenter screen implemented
- [x] Routes configured for notification deep linking
- [x] Tested on physical Android device
- [x] Tested on physical iOS device
- [x] Notification permissions granted by user
- [x] Topics properly configured for targeting
- [x] Notification analytics enabled in Firebase

---

## Next Steps

1. Deploy backend with Firebase Admin SDK integration
2. Configure notification templates for different scenarios:
   - Leave approval/rejection
   - Attendance check-in reminders
   - Payroll notifications
   - Shift change alerts
3. Set up Firebase Cloud Functions for automated notifications
4. Enable Firebase Analytics for notification tracking

---

## Resources

- [Firebase Documentation](https://firebase.google.com/docs/messaging)
- [FlutterFire Messaging](https://firebase.flutter.dev/docs/messaging/overview/)
- [Local Notifications Plugin](https://pub.dev/packages/flutter_local_notifications)

---

**Date**: July 27, 2026  
**Status**: Configuration Guide  
**Version**: 1.0

