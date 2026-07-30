import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';
import 'package:smart_hrms_mobile/core/network/dio_client.dart';
import 'package:smart_hrms_mobile/features/shift/data/models/shift_model.dart';
import 'package:smart_hrms_mobile/features/shift/data/repository/shift_repository.dart';

import 'shift_repository_test.mocks.dart';

@GenerateMocks([DioClient])
void main() {
  late ShiftRepository repository;
  late MockDioClient mockDioClient;

  setUp(() {
    mockDioClient = MockDioClient();
    repository = ShiftRepository(mockDioClient);
  });

  group('ShiftRepository - getMyShift', () {
    test('returns employee current shift', () async {
      // Arrange
      final mockResponse = Response(
        requestOptions: RequestOptions(path: ''),
        statusCode: 200,
        data: {
          'success': true,
          'data': {
            'id': 1,
            'employee_id': 100,
            'shift_id': 1,
            'shift': {
              'id': 1,
              'name': 'Morning Shift',
              'type': 'morning',
              'start_time': '06:00',
              'end_time': '14:00',
              'is_active': true,
            },
            'effective_from': '2024-01-01',
            'effective_to': null,
            'is_current': true,
          },
        },
      );

      when(mockDioClient.get(any)).thenAnswer((_) async => mockResponse);

      // Act
      final result = await repository.getMyShift();

      // Assert
      expect(result.isRight(), true);
      result.fold(
        (failure) => fail('Should not be failure'),
        (shift) {
          expect(shift.shift.name, 'Morning Shift');
          expect(shift.isCurrent, true);
        },
      );
    });

    test('returns Failure on network error', () async {
      // Arrange
      when(mockDioClient.get(any)).thenThrow(
        DioException(
          requestOptions: RequestOptions(path: ''),
          type: DioExceptionType.connectionTimeout,
        ),
      );

      // Act
      final result = await repository.getMyShift();

      // Assert
      expect(result.isLeft(), true);
    });
  });

  group('ShiftRepository - getAvailableShifts', () {
    test('returns list of available shifts for change', () async {
      // Arrange
      final mockResponse = Response(
        requestOptions: RequestOptions(path: ''),
        statusCode: 200,
        data: {
          'success': true,
          'data': [
            {
              'id': 1,
              'name': 'Morning Shift',
              'type': 'morning',
              'start_time': '06:00',
              'end_time': '14:00',
              'is_active': true,
            },
            {
              'id': 2,
              'name': 'Afternoon Shift',
              'type': 'afternoon',
              'start_time': '10:00',
              'end_time': '18:00',
              'is_active': true,
            },
            {
              'id': 3,
              'name': 'Evening Shift',
              'type': 'evening',
              'start_time': '14:00',
              'end_time': '22:00',
              'is_active': true,
            },
          ],
        },
      );

      when(mockDioClient.get(any)).thenAnswer((_) async => mockResponse);

      // Act
      final result = await repository.getAvailableShifts();

      // Assert
      expect(result.isRight(), true);
      result.fold(
        (failure) => fail('Should not be failure'),
        (shifts) {
          expect(shifts.length, 3);
          expect(shifts[0].name, 'Morning Shift');
          // Verify shift times directly
          expect(shifts[1].startTime, '10:00');
          expect(shifts[1].endTime, '18:00');
        },
      );
    });

    test('handles empty available shifts list', () async {
      // Arrange
      final mockResponse = Response(
        requestOptions: RequestOptions(path: ''),
        statusCode: 200,
        data: {
          'success': true,
          'data': [],
        },
      );

      when(mockDioClient.get(any)).thenAnswer((_) async => mockResponse);

      // Act
      final result = await repository.getAvailableShifts();

      // Assert
      expect(result.isRight(), true);
      result.fold(
        (failure) => fail('Should not be failure'),
        (shifts) => expect(shifts.isEmpty, true),
      );
    });
  });

  group('ShiftRepository - requestShiftChange', () {
    test('submits shift change request successfully', () async {
      // Arrange
      final mockResponse = Response(
        requestOptions: RequestOptions(path: ''),
        statusCode: 200,
        data: {
          'success': true,
          'data': {
            'id': 1,
            'employee_id': 100,
            'employee_name': 'John Doe',
            'employee_code': 'EMP001',
            'current_shift_id': 1,
            'current_shift_name': 'Morning Shift',
            'requested_shift_id': 2,
            'requested_shift_name': 'Afternoon Shift',
            'requested_effective_from': '2024-08-01',
            'reason': 'Personal preference',
            'status': 'pending',
            'remarks': null,
            'created_at': '2024-07-28T10:00:00Z',
            'approved_at': null,
          },
        },
      );

      when(mockDioClient.post(any, data: anyNamed('data')))
          .thenAnswer((_) async => mockResponse);

      // Act
      final result = await repository.requestShiftChange(
        requestedShiftId: 2,
        effectiveFrom: DateTime(2024, 8, 1),
        reason: 'Personal preference',
      );

      // Assert
      expect(result.isRight(), true);
      result.fold(
        (failure) => fail('Should not be failure'),
        (request) {
          expect(request.status, 'pending');
          expect(request.requestedShiftName, 'Afternoon Shift');
        },
      );

      // Verify data sent
      verify(mockDioClient.post(
        any,
        data: {
          'requested_shift_id': 2,
          'requested_effective_from': '2024-08-01',
          'reason': 'Personal preference',
        },
      )).called(1);
    });

    test('returns Failure on request error', () async {
      // Arrange
      when(mockDioClient.post(any, data: anyNamed('data'))).thenThrow(
        DioException(
          requestOptions: RequestOptions(path: ''),
          type: DioExceptionType.unknown,
        ),
      );

      // Act
      final result = await repository.requestShiftChange(
        requestedShiftId: 2,
        effectiveFrom: DateTime(2024, 8, 1),
        reason: 'Personal preference',
      );

      // Assert
      expect(result.isLeft(), true);
    });
  });

  group('ShiftRepository - getShiftChangeHistory', () {
    test('returns paginated shift change requests', () async {
      // Arrange
      final mockResponse = Response(
        requestOptions: RequestOptions(path: ''),
        statusCode: 200,
        data: {
          'success': true,
          'data': [
            {
              'id': 1,
              'employee_id': 100,
              'employee_name': 'John Doe',
              'employee_code': 'EMP001',
              'current_shift_id': 1,
              'current_shift_name': 'Morning Shift',
              'requested_shift_id': 2,
              'requested_shift_name': 'Afternoon Shift',
              'requested_effective_from': '2024-08-01',
              'reason': 'Personal preference',
              'status': 'approved',
              'remarks': null,
              'created_at': '2024-07-28T10:00:00Z',
              'approved_at': '2024-07-28T14:00:00Z',
            },
          ],
          'meta': {
            'page': 1,
            'pages': 1,
            'total': 1,
            'per_page': 20,
          },
        },
      );

      when(mockDioClient.get(any, queryParameters: anyNamed('queryParameters')))
          .thenAnswer((_) async => mockResponse);

      // Act
      final result = await repository.getShiftChangeHistory(page: 1, perPage: 20);

      // Assert
      expect(result.isRight(), true);
      result.fold(
        (failure) => fail('Should not be failure'),
        (paginatedResult) {
          expect(paginatedResult.items.length, 1);
          expect(paginatedResult.items[0].status, 'approved');
        },
      );
    });

    test('applies status filter', () async {
      // Arrange
      final mockResponse = Response(
        requestOptions: RequestOptions(path: ''),
        statusCode: 200,
        data: {
          'success': true,
          'data': [],
          'meta': {
            'page': 1,
            'pages': 0,
            'total': 0,
            'per_page': 20,
          },
        },
      );

      when(mockDioClient.get(any, queryParameters: anyNamed('queryParameters')))
          .thenAnswer((_) async => mockResponse);

      // Act
      await repository.getShiftChangeHistory(
        page: 1,
        perPage: 20,
        status: 'pending',
      );

      // Assert
      verify(mockDioClient.get(
        any,
        queryParameters: {
          'page': 1,
          'per_page': 20,
          'status': 'pending',
        },
      )).called(1);
    });
  });

  group('ShiftRepository - manager approval methods', () {
    test('approves shift change request successfully', () async {
      // Arrange
      final mockResponse = Response(
        requestOptions: RequestOptions(path: ''),
        statusCode: 200,
        data: {
          'success': true,
          'data': null,
        },
      );

      when(mockDioClient.post(any, data: anyNamed('data')))
          .thenAnswer((_) async => mockResponse);

      // Act
      final result = await repository.approveShiftChange(
        requestId: 1,
        remarks: 'Approved',
      );

      // Assert
      expect(result.isRight(), true);
    });

    test('rejects shift change with mandatory remarks', () async {
      // Arrange
      final mockResponse = Response(
        requestOptions: RequestOptions(path: ''),
        statusCode: 200,
        data: {
          'success': true,
          'data': null,
        },
      );

      when(mockDioClient.post(any, data: anyNamed('data')))
          .thenAnswer((_) async => mockResponse);

      // Act
      final result = await repository.rejectShiftChange(
        requestId: 1,
        remarks: 'Staffing conflict',
      );

      // Assert
      expect(result.isRight(), true);
      verify(mockDioClient.post(
        any,
        data: {
          'remarks': 'Staffing conflict',
        },
      )).called(1);
    });
  });

  group('ShiftRepository - getShiftChangeApprovals', () {
    test('returns shift change approvals for manager', () async {
      // Arrange
      final mockResponse = Response(
        requestOptions: RequestOptions(path: ''),
        statusCode: 200,
        data: {
          'success': true,
          'data': [
            {
              'id': 1,
              'employee_id': 100,
              'employee_name': 'John Doe',
              'employee_code': 'EMP001',
              'current_shift_id': 1,
              'current_shift_name': 'Morning Shift',
              'requested_shift_id': 2,
              'requested_shift_name': 'Afternoon Shift',
              'requested_effective_from': '2024-08-01',
              'reason': 'Personal preference',
              'status': 'pending',
              'remarks': null,
              'created_at': '2024-07-28T10:00:00Z',
              'approved_at': null,
            },
          ],
          'meta': {
            'page': 1,
            'pages': 1,
            'total': 1,
            'per_page': 20,
          },
        },
      );

      when(mockDioClient.get(any, queryParameters: anyNamed('queryParameters')))
          .thenAnswer((_) async => mockResponse);

      // Act
      final result = await repository.getShiftChangeApprovals(
        page: 1,
        perPage: 20,
      );

      // Assert
      expect(result.isRight(), true);
      result.fold(
        (failure) => fail('Should not be failure'),
        (paginatedResult) {
          expect(paginatedResult.items.length, 1);
          expect(paginatedResult.items[0].status, 'pending');
        },
      );
    });

    test('filters approvals by status', () async {
      // Arrange
      final mockResponse = Response(
        requestOptions: RequestOptions(path: ''),
        statusCode: 200,
        data: {
          'success': true,
          'data': [],
          'meta': {
            'page': 1,
            'pages': 0,
            'total': 0,
            'per_page': 20,
          },
        },
      );

      when(mockDioClient.get(any, queryParameters: anyNamed('queryParameters')))
          .thenAnswer((_) async => mockResponse);

      // Act
      await repository.getShiftChangeApprovals(
        page: 1,
        perPage: 20,
        status: 'pending',
      );

      // Assert
      verify(mockDioClient.get(
        any,
        queryParameters: {
          'page': 1,
          'per_page': 20,
          'status': 'pending',
        },
      )).called(1);
    });
  });

  group('ShiftRepository - cancelShiftChangeRequest', () {
    test('cancels pending shift change request', () async {
      // Arrange
      final mockResponse = Response(
        requestOptions: RequestOptions(path: ''),
        statusCode: 200,
        data: {
          'success': true,
          'data': null,
        },
      );

      when(mockDioClient.post(any)).thenAnswer((_) async => mockResponse);

      // Act
      final result = await repository.cancelShiftChangeRequest(1);

      // Assert
      expect(result.isRight(), true);
    });

    test('returns Failure on cancel error', () async {
      // Arrange
      when(mockDioClient.post(any)).thenThrow(
        DioException(
          requestOptions: RequestOptions(path: ''),
          type: DioExceptionType.unknown,
        ),
      );

      // Act
      final result = await repository.cancelShiftChangeRequest(1);

      // Assert
      expect(result.isLeft(), true);
    });
  });

  group('ShiftRepository - shift type extensions', () {
    test('provides correct shift labels', () {
      // Verify shift type enum and extensions work
      expect(ShiftType.morning.label, 'Morning Shift');
      expect(ShiftType.afternoon.label, 'Afternoon Shift');
      expect(ShiftType.evening.label, 'Evening Shift');
      expect(ShiftType.night.label, 'Night Shift');
      expect(ShiftType.rotating.label, 'Rotating Shift');
    });

    test('provides correct time ranges', () {
      expect(ShiftType.morning.timeRange, '06:00 - 14:00');
      expect(ShiftType.afternoon.timeRange, '10:00 - 18:00');
      expect(ShiftType.evening.timeRange, '14:00 - 22:00');
      expect(ShiftType.night.timeRange, '22:00 - 06:00');
      expect(ShiftType.rotating.timeRange, 'Rotating');
    });
  });
}
