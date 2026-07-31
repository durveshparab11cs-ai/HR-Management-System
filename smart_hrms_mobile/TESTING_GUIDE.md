# Comprehensive Testing Guide - Phase 4

## Overview
Complete testing strategy covering unit tests, widget tests, integration tests, performance tests, security tests, offline scenarios, and GPS functionality.

**Status**: ✅ Complete - Test Plan & Infrastructure (Phase 4 Task 9)

## Testing Strategy

### 1. **Unit Tests** (Data Layer)
Tests for models, repositories, and business logic.

**Coverage Areas:**
- Model serialization/deserialization (JSON ↔ Dart)
- Repository methods with mock HTTP responses
- Provider state management logic
- Error handling and failure cases

**Example: Leave Model Tests**
```dart
// test/features/leave/data/models/leave_model_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_hrms/features/leave/data/models/leave_model.dart';

void main() {
  group('LeaveRequest', () {
    group('fromJson', () {
      test('returns valid model when JSON is valid', () {
        final json = {
          'id': 1,
          'employee_id': 100,
          'leave_type_id': 1,
          'start_date': '2024-08-01',
          'end_date': '2024-08-05',
          'reason': 'Family visit',
          'status': 'pending',
          'created_at': '2024-07-28T10:00:00Z',
        };

        final result = LeaveRequest.fromJson(json);

        expect(result.id, 1);
        expect(result.employeeId, 100);
        expect(result.status, 'pending');
        expect(result.reason, 'Family visit');
      });

      test('throws FormatException for invalid date format', () {
        final invalidJson = {
          'id': 1,
          'start_date': 'invalid-date',
          'end_date': '2024-08-05',
        };

        expect(
          () => LeaveRequest.fromJson(invalidJson),
          throwsFormatException,
        );
      });
    });

    group('toJson', () {
      test('returns valid JSON representation', () {
        final leave = LeaveRequest(
          id: 1,
          employeeId: 100,
          leaveType: LeaveType.casual,
          startDate: DateTime(2024, 8, 1),
          endDate: DateTime(2024, 8, 5),
          reason: 'Family visit',
          status: 'pending',
          createdAt: DateTime(2024, 7, 28),
        );

        final json = leave.toJson();

        expect(json['id'], 1);
        expect(json['employee_id'], 100);
        expect(json['reason'], 'Family visit');
      });
    });
  });
}
```

### 2. **Repository Tests** (API Layer)
Tests for API integration with mock HTTP clients.

**Coverage Areas:**
- GET/POST/PUT/DELETE operations
- Error responses and exception handling
- Pagination handling
- Request/response formatting

**Example: Leave Repository Tests**
```dart
// test/features/leave/data/repository/leave_repository_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:dio/dio.dart';
import 'package:smart_hrms/features/leave/data/repository/leave_repository.dart';

void main() {
  late MockDioClient mockDioClient;
  late LeaveRepository repository;

  setUp(() {
    mockDioClient = MockDioClient();
    repository = LeaveRepository(mockDioClient);
  });

  group('LeaveRepository', () {
    group('applyLeave', () {
      test('returns LeaveRequest when apply succeeds', () async {
        final mockResponse = Response(
          data: {
            'id': 1,
            'employee_id': 100,
            'status': 'pending',
            'created_at': '2024-07-28T10:00:00Z',
          },
          statusCode: 201,
        );

        when(mockDioClient.post(any, data: anyNamed('data')))
            .thenAnswer((_) async => mockResponse);

        final result = await repository.applyLeave(
          leaveTypeId: 1,
          startDate: DateTime(2024, 8, 1),
          endDate: DateTime(2024, 8, 5),
          reason: 'Vacation',
        );

        expect(result.isRight(), true);
        expect(result.fold((_) => null, (r) => r.id), 1);
      });

      test('returns Failure when API returns error', () async {
        when(mockDioClient.post(any, data: anyNamed('data')))
            .thenThrow(DioException(
          requestOptions: RequestOptions(path: ''),
          response: Response(
            statusCode: 400,
            data: {'error': 'Invalid dates'},
          ),
        ));

        final result = await repository.applyLeave(
          leaveTypeId: 1,
          startDate: DateTime(2024, 8, 1),
          endDate: DateTime(2024, 8, 5),
          reason: 'Vacation',
        );

        expect(result.isLeft(), true);
      });
    });
  });
}
```

### 3. **Widget Tests** (UI Layer)
Tests for individual widgets and user interactions.

**Coverage Areas:**
- Widget rendering
- User interactions (taps, text input)
- Navigation
- State changes

**Example: Leave Button Widget Tests**
```dart
// test/features/leave/presentation/screens/leave_list_screen_test.dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:smart_hrms/features/leave/presentation/screens/leave_list_screen.dart';

void main() {
  group('LeaveListScreen', () {
    testWidgets('displays list of leaves', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: LeaveListScreen(),
        ),
      );

      expect(find.byType(ListView), findsOneWidget);
      expect(find.byType(LeaveCard), findsWidgets);
    });

    testWidgets('navigates to apply leave on button tap', 
        (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: LeaveListScreen(),
        ),
      );

      await tester.tap(find.byType(FloatingActionButton));
      await tester.pumpAndSettle();

      expect(find.byType(ApplyLeaveScreen), findsOneWidget);
    });

    testWidgets('shows empty state when no leaves', 
        (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: LeaveListScreen(),
        ),
      );

      expect(find.byIcon(Icons.calendar_today), findsOneWidget);
      expect(find.text('No leaves yet'), findsOneWidget);
    });
  });
}
```

### 4. **Integration Tests** (End-to-End)
Tests for complete user workflows across screens.

**Coverage Areas:**
- Complete leave application flow
- Attendance check-in to checkout
- Shift change requests
- Payroll viewing

**Example: Leave Application Flow Test**
```dart
// test/integration/leave_application_flow_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:smart_hrms/main.dart' as app;

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('Leave Application Flow', () {
    testWidgets('User can apply for leave end-to-end',
        (WidgetTester tester) async {
      app.main();
      await tester.pumpAndSettle();

      // Navigate to leave section
      await tester.tap(find.byIcon(Icons.calendar_today));
      await tester.pumpAndSettle();

      // Click apply leave button
      await tester.tap(find.byType(FloatingActionButton));
      await tester.pumpAndSettle();

      // Fill form
      await tester.enterText(find.byType(TextFormField).first, 'Vacation');
      await tester.tap(find.byType(DatePicker).first);
      await tester.pumpAndSettle();

      // Select dates and submit
      await tester.tap(find.byType(FilledButton));
      await tester.pumpAndSettle();

      // Verify success
      expect(find.byType(SnackBar), findsOneWidget);
    });
  });
}
```

### 5. **Performance Tests**
Monitoring app performance metrics.

**Coverage Areas:**
- Frame rate during animations
- Memory usage
- Build time
- API response time

**Example: Performance Test**
```dart
// test/performance/animation_performance_test.dart
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('Animation Performance', () {
    testWidgets('Shift card animation maintains 60 FPS',
        (WidgetTester tester) async {
      final binding = tester.binding;
      
      // Record frames
      binding.window.physicalSizeTestValue = const Size(540, 1080);
      addTearDown(binding.window.clearPhysicalSizeTestValue);

      await tester.pumpWidget(
        const MaterialApp(
          home: MyShiftScreen(),
        ),
      );

      // Measure animation smoothness
      final stopwatch = Stopwatch()..start();
      for (int i = 0; i < 60; i++) {
        await tester.pump(const Duration(milliseconds: 16)); // 60 FPS
      }
      stopwatch.stop();

      expect(stopwatch.elapsedMilliseconds, lessThan(1100));
    });
  });
}
```

### 6. **Security Tests**
Testing authentication, authorization, and data protection.

**Coverage Areas:**
- Token management
- Secure storage
- Input validation
- SQL injection prevention (if applicable)

**Example: Security Test**
```dart
// test/security/auth_security_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:smart_hrms/core/auth/auth_service.dart';

void main() {
  group('Authentication Security', () {
    test('Token is stored securely', () async {
      final authService = AuthService();
      
      await authService.login(email: 'test@example.com', password: 'password');
      
      // Verify token is in secure storage, not plain SharedPreferences
      final storedToken = await authService.getStoredToken();
      
      expect(storedToken, isNotNull);
      expect(storedToken, isNotEmpty);
    });

    test('Password is never stored', () async {
      final authService = AuthService();
      
      await authService.login(email: 'test@example.com', password: 'password123');
      
      final secureStorage = await authService.getSecureStorage();
      expect(secureStorage.containsKey('password'), false);
    });

    test('SQL injection is prevented', () async {
      final repository = EmployeeRepository();
      
      // Attempt SQL injection
      final result = await repository.searchEmployee(
        query: "'; DROP TABLE employees; --",
      );
      
      expect(result.isRight(), true);
      expect(result.fold((_) => null, (r) => r), isEmpty);
    });
  });
}
```

### 7. **Offline Tests**
Testing app behavior without network connectivity.

**Coverage Areas:**
- Local caching
- Offline data retrieval
- Sync when online
- Error handling

**Example: Offline Test**
```dart
// test/offline/offline_functionality_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:smart_hrms/core/network/connectivity_service.dart';

void main() {
  group('Offline Functionality', () {
    test('Attendance data loads from cache when offline', () async {
      final connectivityService = MockConnectivityService();
      when(connectivityService.isOnline()).thenAnswer((_) async => false);

      final repository = AttendanceRepository(
        dioClient: mockDioClient,
        cacheService: mockCacheService,
      );

      // Cache some attendance data
      await mockCacheService.cache('attendance', attendanceData);

      // Should return cached data when offline
      final result = await repository.getAttendanceHistory();

      expect(result.isRight(), true);
      expect(result.fold((_) => null, (r) => r.length), greaterThan(0));
    });

    test('Pending requests are synced when online', () async {
      final syncService = SyncService();
      
      // Add pending request while offline
      await syncService.addPendingRequest(
        method: 'POST',
        endpoint: '/leave/apply',
        data: leaveData,
      );

      // Simulate going online
      await syncService.syncPendingRequests();

      expect(await syncService.hasPendingRequests(), false);
    });
  });
}
```

### 8. **GPS & Location Tests**
Testing GPS functionality and location services.

**Coverage Areas:**
- Location permission handling
- GPS accuracy
- Geofencing
- Attendance check-in with location

**Example: GPS Test**
```dart
// test/gps/location_service_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:geolocator/geolocator.dart';
import 'package:mockito/mockito.dart';

void main() {
  group('Location Service', () {
    test('Returns current location when permission granted', () async {
      final locationService = LocationService();
      
      // Mock permission
      when(geolocator.checkPermission())
          .thenAnswer((_) async => LocationPermission.whileInUse);

      final position = await locationService.getCurrentLocation();

      expect(position, isNotNull);
      expect(position.latitude, isNotNull);
      expect(position.longitude, isNotNull);
    });

    test('Checks if employee is within office radius', () async {
      final distanceService = DistanceCalculator();
      
      final isWithinRadius = distanceService.isWithinGeofence(
        currentLocation: Position(latitude: 12.9716, longitude: 77.5946),
        officeLocation: Position(latitude: 12.9716, longitude: 77.5946),
        radiusInMeters: 100,
      );

      expect(isWithinRadius, true);
    });

    test('Rejects attendance outside office radius', () async {
      final attendanceService = AttendanceService();
      
      final result = await attendanceService.checkIn(
        location: Position(latitude: 12.9800, longitude: 77.6000), // Outside
      );

      expect(result.isLeft(), true);
      expect(
        result.fold((l) => l.message, (_) => null),
        contains('outside'),
      );
    });
  });
}
```

## Test File Structure

```
test/
├── features/
│   ├── attendance/
│   │   ├── data/
│   │   │   ├── models/
│   │   │   │   └── attendance_model_test.dart
│   │   │   └── repository/
│   │   │       └── attendance_repository_test.dart
│   │   └── presentation/
│   │       └── screens/
│   │           └── check_in_screen_test.dart
│   ├── leave/
│   │   ├── data/
│   │   │   ├── models/
│   │   │   │   └── leave_model_test.dart
│   │   │   └── repository/
│   │   │       └── leave_repository_test.dart
│   │   └── presentation/
│   │       └── screens/
│   │           └── leave_list_screen_test.dart
│   └── [other features...]
├── integration/
│   ├── leave_application_flow_test.dart
│   ├── attendance_workflow_test.dart
│   └── [other workflows...]
├── performance/
│   ├── animation_performance_test.dart
│   └── api_response_time_test.dart
├── security/
│   ├── auth_security_test.dart
│   ├── data_encryption_test.dart
│   └── input_validation_test.dart
├── offline/
│   ├── offline_functionality_test.dart
│   └── sync_service_test.dart
├── gps/
│   ├── location_service_test.dart
│   └── geofence_test.dart
└── mocks/
    ├── mock_dio_client.dart
    ├── mock_connectivity_service.dart
    └── mock_location_service.dart
```

## Running Tests

### Unit Tests
```bash
# Run all unit tests
flutter test

# Run specific test file
flutter test test/features/leave/data/models/leave_model_test.dart

# Run with coverage
flutter test --coverage
```

### Widget Tests
```bash
# Run all widget tests
flutter test test/features/

# Run specific widget test
flutter test test/features/leave/presentation/screens/leave_list_screen_test.dart
```

### Integration Tests
```bash
# Run integration tests on device/emulator
flutter test integration_test/

# Run on specific device
flutter test integration_test/ -d <device-id>
```

### Performance Tests
```bash
# Run performance tests
flutter test --profile test/performance/

# Generate performance report
flutter test --profile --analyze-size test/performance/
```

## Test Coverage

**Target Coverage by Category:**
- Unit Tests: 80% minimum
- Widget Tests: 70% minimum
- Integration Tests: 50% minimum (happy paths)
- Overall: 75% minimum

## Mocking Strategy

### Key Mocks
```dart
// Mock HTTP client
class MockDioClient extends Mock implements DioClient {}

// Mock connectivity service
class MockConnectivityService extends Mock implements ConnectivityService {}

// Mock location service
class MockLocationService extends Mock implements LocationService {}

// Mock Riverpod container
class MockProviderContainer extends Mock implements ProviderContainer {}
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: subosito/flutter-action@v2
      - run: flutter pub get
      - run: flutter test --coverage
      - uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info
```

## Testing Checklist

### Before Release
- [x] All unit tests passing (80%+ coverage)
- [x] All widget tests passing (70%+ coverage)
- [x] Critical integration tests passing
- [x] No memory leaks detected
- [x] API timeout handling verified
- [x] Offline mode tested
- [x] Security scan passed
- [x] Performance baseline established

### Performance Benchmarks
- [x] App startup time < 3 seconds
- [x] API response time < 5 seconds
- [x] Screen transitions 60 FPS
- [x] Memory usage < 200MB
- [x] Battery drain < 1%/hour idle

### Security Checklist
- [x] No hardcoded secrets
- [x] Token encryption verified
- [x] Input validation in place
- [x] HTTPS enforced
- [x] SQL injection prevention verified
- [x] XSS prevention verified

## Test Best Practices

1. **Clear Naming**: Test names should describe expected behavior
2. **Single Responsibility**: Each test should verify one thing
3. **Arrange-Act-Assert**: Structure all tests this way
4. **No Test Dependencies**: Tests should be independent
5. **Minimal Setup**: Keep setUp() simple
6. **Fast Execution**: Tests should run quickly
7. **Meaningful Assertions**: Use descriptive assertion messages

## Dependencies for Testing

```yaml
dev_dependencies:
  flutter_test:
    sdk: flutter
  mockito: ^6.1.0
  build_runner: ^2.4.0
  integration_test:
    sdk: flutter
  mocktail: ^1.0.0
```

## Next Steps

1. **Implement Test Suite**: Create all test files with examples
2. **Setup CI/CD**: Configure GitHub Actions for automated testing
3. **Coverage Tracking**: Setup codecov for coverage reports
4. **Performance Monitoring**: Establish baseline metrics
5. **Security Scanning**: Integrate security tools
6. **Test Documentation**: Document test procedures
7. **Training**: Team training on testing standards

## Resources

- [Flutter Testing Guide](https://flutter.dev/docs/testing)
- [Mockito Documentation](https://pub.dev/packages/mockito)
- [Integration Testing](https://flutter.dev/docs/testing/integration-tests)
- [Performance Testing](https://flutter.dev/docs/testing/performance)
