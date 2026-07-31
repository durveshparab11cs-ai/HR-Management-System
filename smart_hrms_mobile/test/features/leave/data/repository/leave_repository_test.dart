import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';
import 'package:smart_hrms_mobile/core/network/dio_client.dart';
import 'package:smart_hrms_mobile/features/leave/data/repository/leave_repository.dart';

import 'leave_repository_test.mocks.dart';

@GenerateMocks([DioClient])
void main() {
  late LeaveRepository repository;
  late MockDioClient mockDioClient;

  setUp(() {
    mockDioClient = MockDioClient();
    repository = LeaveRepository(mockDioClient);
  });

  group('LeaveRepository - getLeaveTypes', () {
    test('returns list of leave types', () async {
      // Arrange
      final mockResponse = Response(
        requestOptions: RequestOptions(path: ''),
        statusCode: 200,
        data: {
          'success': true,
          'data': [
            {
              'id': 1,
              'name': 'Annual Leave',
              'code': 'AL',
              'max_days': 20,
              'requires_approval': true,
              'description': 'Annual paid leave',
            },
            {
              'id': 2,
              'name': 'Sick Leave',
              'code': 'SL',
              'max_days': 10,
              'requires_approval': false,
            },
          ],
        },
      );

      when(mockDioClient.get(any)).thenAnswer((_) async => mockResponse);

      // Act
      final result = await repository.getLeaveTypes();

      // Assert
      expect(result.isRight(), true);
      result.fold(
        (failure) => fail('Should not be failure'),
        (types) {
          expect(types.length, 2);
          expect(types[0].name, 'Annual Leave');
          expect(types[1].code, 'SL');
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
      final result = await repository.getLeaveTypes();

      // Assert
      expect(result.isLeft(), true);
    });
  });

  group('LeaveRepository - getLeaveBalance', () {
    test('returns leave balance for all leave types', () async {
      // Arrange
      final mockResponse = Response(
        requestOptions: RequestOptions(path: ''),
        statusCode: 200,
        data: {
          'success': true,
          'data': [
            {
              'leave_type_id': 1,
              'leave_type_name': 'Annual Leave',
              'total_days': 20,
              'used_days': 5,
              'remaining_days': 15,
            },
            {
              'leave_type_id': 2,
              'leave_type_name': 'Sick Leave',
              'total_days': 10,
              'used_days': 2,
              'remaining_days': 8,
            },
          ],
        },
      );

      when(mockDioClient.get(any)).thenAnswer((_) async => mockResponse);

      // Act
      final result = await repository.getLeaveBalance();

      // Assert
      expect(result.isRight(), true);
      result.fold(
        (failure) => fail('Should not be failure'),
        (balance) {
          expect(balance.length, 2);
          expect(balance[0].remainingDays, 15);
          expect(balance[1].usedDays, 2);
        },
      );
    });
  });

  group('LeaveRepository - getManagers', () {
    test('returns list of available managers', () async {
      // Arrange
      final mockResponse = Response(
        requestOptions: RequestOptions(path: ''),
        statusCode: 200,
        data: {
          'success': true,
          'data': [
            {
              'id': 1,
              'name': 'Alice Manager',
              'employee_code': 'MGR001',
              'department': 'Engineering',
            },
            {
              'id': 2,
              'name': 'Bob Manager',
              'employee_code': 'MGR002',
              'department': 'HR',
            },
          ],
        },
      );

      when(mockDioClient.get(any)).thenAnswer((_) async => mockResponse);

      // Act
      final result = await repository.getManagers();

      // Assert
      expect(result.isRight(), true);
      result.fold(
        (failure) => fail('Should not be failure'),
        (managers) {
          expect(managers.length, 2);
          expect(managers[0].name, 'Alice Manager');
        },
      );
    });
  });

  group('LeaveRepository - applyLeave', () {
    test('submits full day leave request successfully', () async {
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
            'leave_type_id': 1,
            'leave_type_name': 'Annual Leave',
            'start_date': '2024-08-01',
            'end_date': '2024-08-05',
            'total_days': 5,
            'reason': 'Vacation',
            'status': 'pending',
            'created_at': '2024-07-28T10:00:00Z',
            'is_half_day': false,
            'is_early_leave': false,
          },
        },
      );

      when(mockDioClient.post(any, data: anyNamed('data')))
          .thenAnswer((_) async => mockResponse);

      // Act
      final result = await repository.applyLeave(
        leaveTypeId: 1,
        startDate: DateTime(2024, 8, 1),
        endDate: DateTime(2024, 8, 5),
        reason: 'Vacation',
      );

      // Assert
      expect(result.isRight(), true);
      result.fold(
        (failure) => fail('Should not be failure'),
        (request) {
          expect(request.status, 'pending');
          expect(request.totalDays, 5);
        },
      );
    });

    test('includes approver_id when provided', () async {
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
            'leave_type_id': 1,
            'leave_type_name': 'Annual Leave',
            'start_date': '2024-08-01',
            'end_date': '2024-08-05',
            'total_days': 5,
            'reason': 'Vacation',
            'status': 'pending',
            'approver_id': 2,
            'created_at': '2024-07-28T10:00:00Z',
            'is_half_day': false,
            'is_early_leave': false,
          },
        },
      );

      when(mockDioClient.post(any, data: anyNamed('data')))
          .thenAnswer((_) async => mockResponse);

      // Act
      await repository.applyLeave(
        leaveTypeId: 1,
        startDate: DateTime(2024, 8, 1),
        endDate: DateTime(2024, 8, 5),
        reason: 'Vacation',
        approverId: 2,
      );

      // Assert
      verify(mockDioClient.post(
        any,
        data: {
          'leave_type_id': 1,
          'start_date': '2024-08-01',
          'end_date': '2024-08-05',
          'reason': 'Vacation',
          'approver_id': 2,
        },
      )).called(1);
    });
  });

  group('LeaveRepository - applyHalfDayLeave', () {
    test('submits half day leave request successfully', () async {
      // Arrange
      final mockResponse = Response(
        requestOptions: RequestOptions(path: ''),
        statusCode: 200,
        data: {
          'success': true,
          'data': {
            'id': 2,
            'employee_id': 100,
            'employee_name': 'John Doe',
            'leave_type_id': 1,
            'leave_type_name': 'Annual Leave',
            'start_date': '2024-08-01',
            'end_date': '2024-08-01',
            'total_days': 1,
            'reason': 'Personal work',
            'status': 'pending',
            'is_half_day': true,
            'created_at': '2024-07-28T10:00:00Z',
            'is_early_leave': false,
          },
        },
      );

      when(mockDioClient.post(any, data: anyNamed('data')))
          .thenAnswer((_) async => mockResponse);

      // Act
      final result = await repository.applyHalfDayLeave(
        leaveTypeId: 1,
        date: DateTime(2024, 8, 1),
        reason: 'Personal work',
        halfDayType: 'first_half',
      );

      // Assert
      expect(result.isRight(), true);
      result.fold(
        (failure) => fail('Should not be failure'),
        (request) {
          expect(request.isHalfDay, true);
        },
      );
    });
  });

  group('LeaveRepository - applyEarlyLeave', () {
    test('submits early leave request successfully', () async {
      // Arrange
      final mockResponse = Response(
        requestOptions: RequestOptions(path: ''),
        statusCode: 200,
        data: {
          'success': true,
          'data': {
            'id': 3,
            'employee_id': 100,
            'employee_name': 'John Doe',
            'leave_type_id': 0,
            'leave_type_name': 'Early Leave',
            'start_date': '2024-07-28',
            'end_date': '2024-07-28',
            'total_days': 0,
            'reason': 'Doctor appointment',
            'status': 'pending',
            'is_half_day': false,
            'is_early_leave': true,
            'created_at': '2024-07-28T10:00:00Z',
          },
        },
      );

      when(mockDioClient.post(any, data: anyNamed('data')))
          .thenAnswer((_) async => mockResponse);

      // Act
      final result = await repository.applyEarlyLeave(
        date: DateTime(2024, 7, 28),
        time: '14:30',
        reason: 'Doctor appointment',
      );

      // Assert
      expect(result.isRight(), true);
      result.fold(
        (failure) => fail('Should not be failure'),
        (request) {
          expect(request.isEarlyLeave, true);
        },
      );
    });
  });

  group('LeaveRepository - getMyLeaveRequests', () {
    test('returns paginated leave requests', () async {
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
              'leave_type_id': 1,
              'leave_type_name': 'Annual Leave',
              'start_date': '2024-08-01',
              'end_date': '2024-08-05',
              'total_days': 5,
              'reason': 'Vacation',
              'status': 'approved',
              'created_at': '2024-07-28T10:00:00Z',
              'is_half_day': false,
              'is_early_leave': false,
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
      final result =
          await repository.getMyLeaveRequests(page: 1, perPage: 20);

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
      await repository.getMyLeaveRequests(page: 1, perPage: 20, status: 'pending');

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

  group('LeaveRepository - approval methods', () {
    test('approves leave request successfully', () async {
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
      final result = await repository.approveLeaveRequest(
        id: 1,
        remarks: 'Approved',
      );

      // Assert
      expect(result.isRight(), true);
    });

    test('rejects leave request with mandatory remarks', () async {
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
      final result = await repository.rejectLeaveRequest(
        id: 1,
        remarks: 'Cannot approve at this time',
      );

      // Assert
      expect(result.isRight(), true);
      verify(mockDioClient.post(
        any,
        data: {
          'remarks': 'Cannot approve at this time',
        },
      )).called(1);
    });
  });

  group('LeaveRepository - cancelLeaveRequest', () {
    test('cancels leave request successfully', () async {
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
      final result = await repository.cancelLeaveRequest(1);

      // Assert
      expect(result.isRight(), true);
    });
  });

  group('LeaveRepository - getLeaveApprovals', () {
    test('returns leave approvals for manager', () async {
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
              'leave_type_id': 1,
              'leave_type_name': 'Annual Leave',
              'start_date': '2024-08-01',
              'end_date': '2024-08-05',
              'total_days': 5,
              'reason': 'Vacation',
              'status': 'pending',
              'created_at': '2024-07-28T10:00:00Z',
              'is_half_day': false,
              'is_early_leave': false,
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
      final result = await repository.getLeaveApprovals(page: 1, perPage: 20);

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
  });
}
