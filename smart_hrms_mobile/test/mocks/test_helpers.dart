import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

/// Helper to wrap widget with necessary providers and theme
ProviderContainer createProviderContainer({
  ProviderContainer? parent,
  List<Override> overrides = const [],
}) {
  return ProviderContainer(
    parent: parent,
    overrides: overrides,
  );
}

/// Helper to test widgets with Material Design 3 theme
Future<void> pumpWidget(
  WidgetTester tester,
  Widget widget, {
  bool isDarkMode = false,
}) async {
  await tester.pumpWidget(
    MaterialApp(
      home: widget,
      theme: ThemeData(useMaterial3: true),
      darkTheme: ThemeData.dark(useMaterial3: true),
      themeMode: isDarkMode ? ThemeMode.dark : ThemeMode.light,
    ),
  );
}

/// Helper to test widgets wrapped with Riverpod
Future<void> pumpConsumerWidget(
  WidgetTester tester,
  Widget widget, {
  ProviderContainer? providerContainer,
  List<Override> overrides = const [],
}) async {
  final container = providerContainer ?? 
      createProviderContainer(overrides: overrides);

  await tester.pumpWidget(
    MaterialApp(
      home: UncontrolledProviderScope(
        container: container,
        child: widget,
      ),
      theme: ThemeData(useMaterial3: true),
      darkTheme: ThemeData.dark(useMaterial3: true),
    ),
  );
}

/// Helper to wait for widget to settle (animations complete)
Future<void> pumpAndSettle(WidgetTester tester) async {
  await tester.pumpAndSettle();
}

/// Helper to find text in widget tree
Finder findText(String text) => find.text(text);

/// Helper to find button with text
Finder findButton(String text) => find.byWidgetPredicate(
  (widget) => widget is MaterialButton && 
      widget.child is Text && 
      (widget.child as Text).data == text,
);

/// Helper to verify async operation completes
Future<void> expectAsyncCompletion(
  Future Function() asyncOperation, {
  Duration timeout = const Duration(seconds: 5),
}) async {
  expect(
    asyncOperation(),
    completes,
  );
}

/// Helper to create mock HTTP response
Map<String, dynamic> createMockResponse({
  required int statusCode,
  required Map<String, dynamic> data,
}) {
  return {
    'statusCode': statusCode,
    'data': data,
  };
}

/// Helper to create mock leave request
Map<String, dynamic> createMockLeaveRequest({
  int id = 1,
  int employeeId = 100,
  int leaveTypeId = 1,
  String startDate = '2024-08-01',
  String endDate = '2024-08-05',
  String reason = 'Vacation',
  String status = 'pending',
}) {
  return {
    'id': id,
    'employee_id': employeeId,
    'leave_type_id': leaveTypeId,
    'start_date': startDate,
    'end_date': endDate,
    'reason': reason,
    'status': status,
    'created_at': '2024-07-28T10:00:00Z',
    'updated_at': '2024-07-28T10:00:00Z',
  };
}

/// Helper to create mock shift data
Map<String, dynamic> createMockShift({
  int id = 1,
  String name = 'Morning',
  String startTime = '09:00',
  String endTime = '17:00',
  String status = 'active',
}) {
  return {
    'id': id,
    'name': name,
    'start_time': startTime,
    'end_time': endTime,
    'status': status,
    'created_at': '2024-01-01T00:00:00Z',
  };
}

/// Helper to create mock payroll data
Map<String, dynamic> createMockPayslip({
  int id = 1,
  int employeeId = 100,
  String month = '2024-07',
  double baseSalary = 50000,
  double deductions = 5000,
  double netSalary = 45000,
  String status = 'processed',
}) {
  return {
    'id': id,
    'employee_id': employeeId,
    'month': month,
    'base_salary': baseSalary,
    'allowances': 2000,
    'deductions': deductions,
    'net_salary': netSalary,
    'status': status,
    'generated_at': '2024-08-01T10:00:00Z',
  };
}

/// Helper to create mock attendance data
Map<String, dynamic> createMockAttendance({
  int id = 1,
  int employeeId = 100,
  String checkInTime = '09:00:00',
  String checkOutTime = '17:00:00',
  double latitude = 12.9716,
  double longitude = 77.5946,
  String status = 'present',
}) {
  return {
    'id': id,
    'employee_id': employeeId,
    'date': '2024-07-28',
    'check_in_time': checkInTime,
    'check_out_time': checkOutTime,
    'check_in_location': {
      'latitude': latitude,
      'longitude': longitude,
    },
    'status': status,
    'created_at': '2024-07-28T09:00:00Z',
  };
}

/// Helper to create mock report data
Map<String, dynamic> createMockReport({
  String type = 'attendance',
  String period = '2024-07',
  int totalDays = 22,
  int presentDays = 20,
  int absentDays = 2,
}) {
  return {
    'type': type,
    'period': period,
    'total_days': totalDays,
    'present_days': presentDays,
    'absent_days': absentDays,
    'attendance_percentage': ((presentDays / totalDays) * 100).toStringAsFixed(2),
  };
}

/// Helper to verify exception is thrown with specific message
Future<void> expectExceptionWithMessage(
  Future Function() asyncOperation,
  String expectedMessage,
) async {
  try {
    await asyncOperation();
    fail('Expected exception was not thrown');
  } catch (e) {
    expect(e.toString(), contains(expectedMessage));
  }
}

/// Helper to measure operation duration
Future<Duration> measureDuration(
  Future Function() operation,
) async {
  final stopwatch = Stopwatch()..start();
  await operation();
  stopwatch.stop();
  return stopwatch.elapsed;
}

/// Helper to create test fixtures directory
void createTestFixtures() {
  // Can be used to setup temporary test files/directories
}

/// Helper to cleanup test fixtures
void cleanupTestFixtures() {
  // Can be used to cleanup temporary test files/directories
}
