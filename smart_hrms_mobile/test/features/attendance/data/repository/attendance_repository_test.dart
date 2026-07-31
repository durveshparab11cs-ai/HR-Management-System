import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';
import 'package:smart_hrms_mobile/core/network/dio_client.dart';
import 'package:smart_hrms_mobile/features/attendance/data/repository/attendance_repository.dart';

import 'attendance_repository_test.mocks.dart';

@GenerateMocks([DioClient])
void main() {
  late AttendanceRepository repository;
  late MockDioClient mockDioClient;

  setUp(() {
    mockDioClient = MockDioClient();
    repository = AttendanceRepository(mockDioClient);
  });

  group('AttendanceRepository - getTodayAttendance', () {
    test('returns TodayAttendance when successful', () async {
      // Arrange
      final mockResponse = Response(
        requestOptions: RequestOptions(path: ''),
        statusCode: 200,
        data: {
          'success': true,
          'data': {
            'has_checked_in': true,
            'has_checked_out': false,
            'check_in_time': '09:00:00',
            'check_out_time': null,
            'total_hours': null,
            'status': 'Checked In',
          },
        },
      );

      when(mockDioClient.get(any)).thenAnswer((_) async => mockResponse);

      // Act
      final result = await repository.getTodayAttendance();

      // Assert
      expect(result.isRight(), true);
      result.fold(
        (failure) => fail('Should not be failure'),
        (attendance) {
          expect(attendance.hasCheckedIn, true);
          expect(attendance.hasCheckedOut, false);
          expect(attendance.status, 'Checked In');
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
      final result = await repository.getTodayAttendance();

      // Assert
      expect(result.isLeft(), true);
    });
  });

  group('AttendanceRepository - checkIn', () {
    test('returns success response on check-in', () async {
      // Arrange
      final mockResponse = Response(
        requestOptions: RequestOptions(path: ''),
        statusCode: 200,
        data: {
          'success': true,
          'data': {
            'message': 'Checked in successfully',
            'timestamp': '2024-07-28T09:00:00Z',
          },
        },
      );

      when(mockDioClient.post(any, data: anyNamed('data')))
          .thenAnswer((_) async => mockResponse);

      // Act
      final result = await repository.checkIn(
        latitude: 12.9716,
        longitude: 77.5946,
      );

      // Assert
      expect(result.isRight(), true);
      result.fold(
        (failure) => fail('Should not be failure'),
        (response) {
          expect(response['message'], 'Checked in successfully');
        },
      );

      // Verify the correct data was sent
      verify(mockDioClient.post(
        any,
        data: {
          'latitude': 12.9716,
          'longitude': 77.5946,
        },
      )).called(1);
    });

    test('returns Failure on check-in error', () async {
      // Arrange
      when(mockDioClient.post(any, data: anyNamed('data'))).thenThrow(
        DioException(
          requestOptions: RequestOptions(path: ''),
          type: DioExceptionType.unknown,
          error: 'Outside geofence',
        ),
      );

      // Act
      final result = await repository.checkIn(
        latitude: 15.0,
        longitude: 75.0,
      );

      // Assert
      expect(result.isLeft(), true);
    });
  });

  group('AttendanceRepository - checkOut', () {
    test('returns success response on check-out', () async {
      // Arrange
      final mockResponse = Response(
        requestOptions: RequestOptions(path: ''),
        statusCode: 200,
        data: {
          'success': true,
          'data': {
            'message': 'Checked out successfully',
            'total_hours': '8.5',
          },
        },
      );

      when(mockDioClient.post(any, data: anyNamed('data')))
          .thenAnswer((_) async => mockResponse);

      // Act
      final result = await repository.checkOut(
        latitude: 12.9716,
        longitude: 77.5946,
      );

      // Assert
      expect(result.isRight(), true);
      result.fold(
        (failure) => fail('Should not be failure'),
        (response) {
          expect(response['message'], 'Checked out successfully');
          expect(response['total_hours'], '8.5');
        },
      );
    });

    test('returns Failure on check-out error', () async {
      // Arrange
      when(mockDioClient.post(any, data: anyNamed('data'))).thenThrow(
        DioException(
          requestOptions: RequestOptions(path: ''),
          response: Response(
            requestOptions: RequestOptions(path: ''),
            statusCode: 400,
            data: {'message': 'Not checked in today'},
          ),
        ),
      );

      // Act
      final result = await repository.checkOut(
        latitude: 12.9716,
        longitude: 77.5946,
      );

      // Assert
      expect(result.isLeft(), true);
    });
  });

  group('AttendanceRepository - uploadCheckInPhoto', () {
    test('returns photo path on successful upload', () async {
      // Arrange
      final mockFile = File('test/fixtures/photo.jpg');
      final mockResponse = Response(
        requestOptions: RequestOptions(path: ''),
        statusCode: 200,
        data: {
          'success': true,
          'data': {'photo_path': '/uploads/photos/checkin_12345.jpg'},
        },
      );

      when(mockDioClient.uploadFile(any, any, fieldName: anyNamed('fieldName')))
          .thenAnswer((_) async => mockResponse);

      // Act
      final result = await repository.uploadCheckInPhoto(mockFile);

      // Assert
      expect(result.isRight(), true);
      result.fold(
        (failure) => fail('Should not be failure'),
        (photoPath) {
          expect(photoPath, '/uploads/photos/checkin_12345.jpg');
        },
      );
    });

    test('returns Failure on upload error', () async {
      // Arrange
      final mockFile = File('test/fixtures/photo.jpg');
      when(mockDioClient.uploadFile(any, any, fieldName: anyNamed('fieldName')))
          .thenThrow(
        DioException(
          requestOptions: RequestOptions(path: ''),
          type: DioExceptionType.connectionTimeout,
        ),
      );

      // Act
      final result = await repository.uploadCheckInPhoto(mockFile);

      // Assert
      expect(result.isLeft(), true);
    });
  });

  group('AttendanceRepository - uploadCheckOutPhoto', () {
    test('returns photo path on successful upload', () async {
      // Arrange
      final mockFile = File('test/fixtures/photo.jpg');
      final mockResponse = Response(
        requestOptions: RequestOptions(path: ''),
        statusCode: 200,
        data: {
          'success': true,
          'data': {'photo_path': '/uploads/photos/checkout_12345.jpg'},
        },
      );

      when(mockDioClient.uploadFile(any, any, fieldName: anyNamed('fieldName')))
          .thenAnswer((_) async => mockResponse);

      // Act
      final result = await repository.uploadCheckOutPhoto(mockFile);

      // Assert
      expect(result.isRight(), true);
      result.fold(
        (failure) => fail('Should not be failure'),
        (photoPath) {
          expect(photoPath, '/uploads/photos/checkout_12345.jpg');
        },
      );
    });
  });

  group('AttendanceRepository - getAttendanceHistory', () {
    test('returns paginated attendance records', () async {
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
              'date': '2024-07-28',
              'check_in': '09:00:00',
              'check_out': '17:00:00',
              'total_hours': '8.0',
              'status': 'Present',
              'latitude': 12.9716,
              'longitude': 77.5946,
            },
            {
              'id': 2,
              'employee_id': 100,
              'employee_name': 'John Doe',
              'date': '2024-07-27',
              'check_in': '09:15:00',
              'check_out': '17:30:00',
              'total_hours': '8.25',
              'status': 'Present',
              'latitude': 12.9716,
              'longitude': 77.5946,
            },
          ],
          'meta': {
            'page': 1,
            'pages': 5,
            'total': 100,
            'per_page': 20,
          },
        },
      );

      when(mockDioClient.get(any, queryParameters: anyNamed('queryParameters')))
          .thenAnswer((_) async => mockResponse);

      // Act
      final result = await repository.getAttendanceHistory(page: 1, perPage: 20);

      // Assert
      expect(result.isRight(), true);
      result.fold(
        (failure) => fail('Should not be failure'),
        (paginatedResult) {
          expect(paginatedResult.items.length, 2);
          expect(paginatedResult.items[0].employeeName, 'John Doe');
          expect(paginatedResult.items[0].status, 'Present');
        },
      );
    });

    test('applies filters correctly', () async {
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
      await repository.getAttendanceHistory(
        page: 1,
        perPage: 20,
        startDate: '2024-07-01',
        endDate: '2024-07-31',
        status: 'Present',
      );

      // Assert - Verify filters were sent
      verify(mockDioClient.get(
        any,
        queryParameters: {
          'page': 1,
          'per_page': 20,
          'start_date': '2024-07-01',
          'end_date': '2024-07-31',
          'status': 'Present',
        },
      )).called(1);
    });

    test('returns Failure on error', () async {
      // Arrange
      when(mockDioClient.get(any, queryParameters: anyNamed('queryParameters')))
          .thenThrow(
        DioException(
          requestOptions: RequestOptions(path: ''),
          type: DioExceptionType.unknown,
        ),
      );

      // Act
      final result = await repository.getAttendanceHistory();

      // Assert
      expect(result.isLeft(), true);
    });
  });

  group('AttendanceRepository - getOfficeSettings', () {
    test('returns office settings successfully', () async {
      // Arrange
      final mockResponse = Response(
        requestOptions: RequestOptions(path: ''),
        statusCode: 200,
        data: {
          'success': true,
          'data': {
            'id': 1,
            'latitude': 12.9716,
            'longitude': 77.5946,
            'radius_meters': 100,
            'office_name': 'Main Office',
            'address': '123 Business Street',
          },
        },
      );

      when(mockDioClient.get(any)).thenAnswer((_) async => mockResponse);

      // Act
      final result = await repository.getOfficeSettings();

      // Assert
      expect(result.isRight(), true);
      result.fold(
        (failure) => fail('Should not be failure'),
        (settings) {
          expect(settings.latitude, 12.9716);
          expect(settings.longitude, 77.5946);
          expect(settings.radiusMeters, 100);
          expect(settings.officeName, 'Main Office');
        },
      );
    });

    test('returns Failure on error', () async {
      // Arrange
      when(mockDioClient.get(any)).thenThrow(
        DioException(
          requestOptions: RequestOptions(path: ''),
          type: DioExceptionType.unknown,
        ),
      );

      // Act
      final result = await repository.getOfficeSettings();

      // Assert
      expect(result.isLeft(), true);
    });
  });
}
