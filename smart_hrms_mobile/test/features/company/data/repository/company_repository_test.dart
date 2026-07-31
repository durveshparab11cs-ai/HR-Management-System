import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';
import 'package:dio/dio.dart';

import 'package:smart_hrms_mobile/core/network/dio_client.dart';
import 'package:smart_hrms_mobile/features/company/data/models/master_data_model.dart';
import 'package:smart_hrms_mobile/features/company/data/repository/company_repository.dart';
import 'package:smart_hrms_mobile/core/error/failures.dart';

import 'company_repository_test.mocks.dart';

@GenerateMocks([DioClient])
void main() {
  late MockDioClient mockDioClient;
  late CompanyRepository repository;

  setUp(() {
    mockDioClient = MockDioClient();
    repository = CompanyRepository(dioClient: mockDioClient);
  });

  group('CompanyRepository', () {
    group('getDepartments', () {
      test('returns list of departments from PostgreSQL', () async {
        // Arrange: Mock response from Flask API
        final mockResponse = Response(
          data: {
            'status': 'success',
            'data': [
              {
                'id': 1,
                'name': 'Medical',
                'code': 'MED',
                'description': 'Medical department',
                'color': '#1a3c6e',
                'is_active': true,
              },
              {
                'id': 2,
                'name': 'Nursing',
                'code': 'NRS',
                'description': 'Nursing department',
                'color': '#0066cc',
                'is_active': true,
              },
            ],
          },
          statusCode: 200,
          requestOptions: RequestOptions(path: ''),
        );

        when(mockDioClient.get('/company/departments')).thenAnswer(
          (_) => Future.value(mockResponse),
        );

        // Act
        final result = await repository.getDepartments();

        // Assert: Verify departments are fetched from API
        expect(result.isRight(), true);
        result.fold(
          (_) => fail('Should return Right'),
          (departments) {
            expect(departments.length, 2);
            expect(departments[0].name, 'Medical');
            expect(departments[1].name, 'Nursing');
            expect(departments[0].code, 'MED');
          },
        );

        verify(mockDioClient.get('/company/departments')).called(1);
      });

      test('returns network failure on API error', () async {
        // Arrange: Mock network error
        when(mockDioClient.get('/company/departments')).thenThrow(
          DioException(
            requestOptions: RequestOptions(path: ''),
            type: DioExceptionType.connectionTimeout,
          ),
        );

        // Act
        final result = await repository.getDepartments();

        // Assert
        expect(result.isLeft(), true);
        result.fold(
          (failure) => expect(failure, isA<NetworkFailure>()),
          (_) => fail('Should return Left'),
        );
      });

      test('handles empty departments list', () async {
        // Arrange: No departments
        final mockResponse = Response(
          data: {
            'status': 'success',
            'data': [],
          },
          statusCode: 200,
          requestOptions: RequestOptions(path: ''),
        );

        when(mockDioClient.get('/company/departments')).thenAnswer(
          (_) => Future.value(mockResponse),
        );

        // Act
        final result = await repository.getDepartments();

        // Assert
        expect(result.isRight(), true);
        result.fold(
          (_) => fail('Should return Right'),
          (departments) => expect(departments.length, 0),
        );
      });
    });

    group('getPositions', () {
      test('returns list of positions from PostgreSQL', () async {
        // Arrange
        final mockResponse = Response(
          data: {
            'status': 'success',
            'data': [
              {
                'id': 1,
                'title': 'Senior Doctor',
                'code': 'SD001',
                'department_id': 1,
                'grade': 'A',
                'description': 'Senior medical professional',
                'is_active': true,
              },
            ],
          },
          statusCode: 200,
          requestOptions: RequestOptions(path: ''),
        );

        when(mockDioClient.get('/company/positions')).thenAnswer(
          (_) => Future.value(mockResponse),
        );

        // Act
        final result = await repository.getPositions();

        // Assert
        expect(result.isRight(), true);
        result.fold(
          (_) => fail('Should return Right'),
          (positions) {
            expect(positions.length, 1);
            expect(positions[0].title, 'Senior Doctor');
          },
        );
      });
    });

    group('getShifts', () {
      test('returns all shifts from PostgreSQL (no hardcoded lists)', () async {
        // Arrange: Mock production shifts from database
        final mockResponse = Response(
          data: {
            'status': 'success',
            'data': [
              {
                'id': 1,
                'name': 'Morning Shift',
                'code': 'MORN',
                'type': 'morning',
                'start_time': '06:00',
                'end_time': '14:00',
                'grace_minutes': 10,
                'break_minutes': 60,
                'working_days': 'Mon-Fri',
                'is_night_shift': false,
                'is_active': true,
              },
              {
                'id': 2,
                'name': 'Afternoon Shift',
                'code': 'AFT',
                'type': 'afternoon',
                'start_time': '10:00',
                'end_time': '18:00',
                'grace_minutes': 10,
                'break_minutes': 60,
                'working_days': 'Mon-Fri',
                'is_night_shift': false,
                'is_active': true,
              },
              {
                'id': 3,
                'name': 'Evening Shift',
                'code': 'EVE',
                'type': 'evening',
                'start_time': '14:00',
                'end_time': '22:00',
                'grace_minutes': 10,
                'break_minutes': 60,
                'working_days': 'Mon-Fri',
                'is_night_shift': false,
                'is_active': true,
              },
              {
                'id': 4,
                'name': 'Night Shift',
                'code': 'NIGHT',
                'type': 'night',
                'start_time': '22:00',
                'end_time': '06:00',
                'grace_minutes': 10,
                'break_minutes': 60,
                'working_days': 'Mon-Fri',
                'is_night_shift': true,
                'is_active': true,
              },
              {
                'id': 5,
                'name': 'Rotating Shift',
                'code': 'ROT',
                'type': 'rotating',
                'start_time': 'varies',
                'end_time': 'varies',
                'grace_minutes': 15,
                'break_minutes': 45,
                'working_days': 'Rotating',
                'is_night_shift': false,
                'is_active': true,
              },
            ],
          },
          statusCode: 200,
          requestOptions: RequestOptions(path: ''),
        );

        when(mockDioClient.get('/company/shifts')).thenAnswer(
          (_) => Future.value(mockResponse),
        );

        // Act
        final result = await repository.getShifts();

        // Assert: All shifts come from API, not hardcoded
        expect(result.isRight(), true);
        result.fold(
          (_) => fail('Should return Right'),
          (shifts) {
            expect(shifts.length, 5);
            expect(shifts[0].name, 'Morning Shift');
            expect(shifts[1].name, 'Afternoon Shift');
            expect(shifts[2].name, 'Evening Shift');
            expect(shifts[3].name, 'Night Shift');
            expect(shifts[4].name, 'Rotating Shift');
            
            // Verify times come from database
            expect(shifts[0].startTime, '06:00');
            expect(shifts[0].endTime, '14:00');
          },
        );

        verify(mockDioClient.get('/company/shifts')).called(1);
      });

      test('handles new shift added on website', () async {
        // Scenario: Admin adds new shift in website admin panel
        // It should immediately appear in mobile app on next fetch
        final mockResponse = Response(
          data: {
            'status': 'success',
            'data': [
              {
                'id': 6,
                'name': 'Custom Shift',
                'code': 'CUST',
                'type': 'custom',
                'start_time': '07:00',
                'end_time': '15:00',
                'grace_minutes': 5,
                'break_minutes': 45,
                'working_days': 'Mon-Thu',
                'is_night_shift': false,
                'is_active': true,
              },
            ],
          },
          statusCode: 200,
          requestOptions: RequestOptions(path: ''),
        );

        when(mockDioClient.get('/company/shifts')).thenAnswer(
          (_) => Future.value(mockResponse),
        );

        final result = await repository.getShifts();

        expect(result.isRight(), true);
        result.fold(
          (_) => fail('Should return Right'),
          (shifts) {
            expect(shifts.length, 1);
            expect(shifts[0].name, 'Custom Shift');
            expect(shifts[0].id, 6); // New ID from database
          },
        );
      });
    });

    group('getDepartmentStats', () {
      test('returns department statistics from PostgreSQL', () async {
        // Arrange
        final mockResponse = Response(
          data: {
            'status': 'success',
            'data': [
              {
                'name': 'Medical',
                'color': '#1a3c6e',
                'count': 25,
              },
              {
                'name': 'Nursing',
                'color': '#0066cc',
                'count': 40,
              },
            ],
          },
          statusCode: 200,
          requestOptions: RequestOptions(path: ''),
        );

        when(mockDioClient.get('/company/department-stats')).thenAnswer(
          (_) => Future.value(mockResponse),
        );

        // Act
        final result = await repository.getDepartmentStats();

        // Assert
        expect(result.isRight(), true);
        result.fold(
          (_) => fail('Should return Right'),
          (stats) {
            expect(stats.length, 2);
            expect(stats[0].name, 'Medical');
            expect(stats[0].count, 25);
            expect(stats[1].count, 40);
          },
        );
      });
    });

    group('Single Source of Truth Verification', () {
      test('all departments come from Flask API (not hardcoded)', () async {
        // This test verifies that departments are NOT hardcoded
        // and always come from the Flask backend

        // Mock response with production data
        final mockResponse = Response(
          data: {
            'status': 'success',
            'data': [
              {'id': 1, 'name': 'Dept A', 'code': 'DA', 'is_active': true},
              {'id': 2, 'name': 'Dept B', 'code': 'DB', 'is_active': true},
              {'id': 3, 'name': 'Dept C', 'code': 'DC', 'is_active': true},
            ],
          },
          statusCode: 200,
          requestOptions: RequestOptions(path: ''),
        );

        when(mockDioClient.get('/company/departments')).thenAnswer(
          (_) => Future.value(mockResponse),
        );

        final result = await repository.getDepartments();

        result.fold(
          (_) => fail('Should succeed'),
          (departments) {
            // Verify these are database values, not hardcoded
            expect(departments, isNotEmpty);
            // If departments were hardcoded, this test would fail
            // because hardcoded values wouldn't match our mock data
            expect(departments[0].name, 'Dept A');
            expect(departments[1].name, 'Dept B');
            expect(departments[2].name, 'Dept C');
          },
        );
      });

      test('shift changes on website appear immediately in app', () async {
        // Simulate: Admin changes shift times on website
        // Expected: Mobile app sees new times immediately on refresh

        final oldShiftData = Response(
          data: {
            'status': 'success',
            'data': [
              {
                'id': 1,
                'name': 'Morning',
                'code': 'MORN',
                'type': 'morning',
                'start_time': '06:00',
                'end_time': '14:00',
                'grace_minutes': 10,
                'break_minutes': 60,
                'working_days': 'Mon-Fri',
                'is_night_shift': false,
                'is_active': true,
              },
            ],
          },
          statusCode: 200,
          requestOptions: RequestOptions(path: ''),
        );

        // Step 1: First fetch (before website change)
        when(mockDioClient.get('/company/shifts')).thenAnswer(
          (_) => Future.value(oldShiftData),
        );

        var result = await repository.getShifts();
        result.fold(
          (_) => fail('Should succeed'),
          (shifts) => expect(shifts[0].startTime, '06:00'),
        );

        // Step 2: Admin changes shift on website to 07:00 - 15:00
        final newShiftData = Response(
          data: {
            'status': 'success',
            'data': [
              {
                'id': 1,
                'name': 'Morning',
                'code': 'MORN',
                'type': 'morning',
                'start_time': '07:00',
                'end_time': '15:00',
                'grace_minutes': 10,
                'break_minutes': 60,
                'working_days': 'Mon-Fri',
                'is_night_shift': false,
                'is_active': true,
              },
            ],
          },
          statusCode: 200,
          requestOptions: RequestOptions(path: ''),
        );

        // Step 3: Second fetch (after website change)
        when(mockDioClient.get('/company/shifts')).thenAnswer(
          (_) => Future.value(newShiftData),
        );

        result = await repository.getShifts();
        result.fold(
          (_) => fail('Should succeed'),
          (shifts) {
            // New time immediately visible
            expect(shifts[0].startTime, '07:00');
            expect(shifts[0].endTime, '15:00');
          },
        );
      });
    });
  });
}
