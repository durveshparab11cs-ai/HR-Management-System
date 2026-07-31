import 'package:flutter_test/flutter_test.dart';
import 'package:smart_hrms_mobile/features/attendance/data/models/attendance_model.dart';

void main() {
  group('AttendanceRecord Model Tests', () {
    group('fromJson', () {
      test('parses attendance record correctly', () {
        final json = {
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
          'check_in_photo_path': '/photos/checkin.jpg',
          'check_out_photo_path': '/photos/checkout.jpg',
          'remarks': null,
        };

        final record = AttendanceRecord.fromJson(json);

        expect(record.id, 1);
        expect(record.employeeId, 100);
        expect(record.employeeName, 'John Doe');
        expect(record.status, 'Present');
        expect(record.checkIn, '09:00:00');
        expect(record.checkOut, '17:00:00');
      });

      test('handles missing optional fields', () {
        final json = {
          'id': 2,
          'employee_id': 101,
          'employee_name': 'Jane Smith',
          'date': '2024-07-29',
          'check_in': '09:15:00',
          'check_out': null,
          'total_hours': null,
          'status': 'Working',
          'latitude': null,
          'longitude': null,
        };

        final record = AttendanceRecord.fromJson(json);

        expect(record.checkOut, isNull);
        expect(record.latitude, isNull);
        expect(record.status, 'Working');
      });

      test('parses location coordinates correctly', () {
        final json = {
          'id': 3,
          'employee_id': 102,
          'employee_name': 'Bob Wilson',
          'date': '2024-07-30',
          'check_in': '08:45:00',
          'check_out': '17:30:00',
          'total_hours': '8.75',
          'status': 'Present',
          'latitude': 12.9716,
          'longitude': 77.5946,
        };

        final record = AttendanceRecord.fromJson(json);

        expect(record.latitude, 12.9716);
        expect(record.longitude, 77.5946);
      });
    });

    group('toJson', () {
      test('converts attendance record to JSON', () {
        final record = AttendanceRecord(
          id: 1,
          employeeId: 100,
          employeeName: 'John Doe',
          date: '2024-07-28',
          checkIn: '09:00:00',
          checkOut: '17:00:00',
          totalHours: '8.0',
          status: 'Present',
          latitude: 12.9716,
          longitude: 77.5946,
          checkInPhotoPath: '/photos/checkin.jpg',
          checkOutPhotoPath: '/photos/checkout.jpg',
        );

        final json = record.toJson();

        expect(json['id'], 1);
        expect(json['employee_id'], 100);
        expect(json['employee_name'], 'John Doe');
        expect(json['date'], '2024-07-28');
        expect(json['status'], 'Present');
      });
    });

    group('Status validation', () {
      test('validates Present status', () {
        final record = AttendanceRecord(
          id: 1,
          employeeId: 100,
          employeeName: 'John Doe',
          date: '2024-07-28',
          checkIn: '09:00:00',
          checkOut: '17:00:00',
          status: 'Present',
        );

        expect(record.status, 'Present');
      });

      test('validates Absent status', () {
        final record = AttendanceRecord(
          id: 2,
          employeeId: 101,
          employeeName: 'Jane Smith',
          date: '2024-07-28',
          status: 'Absent',
        );

        expect(record.status, 'Absent');
      });

      test('validates Working status', () {
        final record = AttendanceRecord(
          id: 3,
          employeeId: 102,
          employeeName: 'Bob Wilson',
          date: '2024-07-28',
          checkIn: '09:00:00',
          status: 'Working',
        );

        expect(record.status, 'Working');
      });
    });
  });

  group('TodayAttendance Model Tests', () {
    group('fromJson', () {
      test('parses today attendance correctly', () {
        final json = {
          'has_checked_in': true,
          'has_checked_out': false,
          'check_in_time': '09:00:00',
          'check_out_time': null,
          'total_hours': null,
          'status': 'Checked In',
        };

        final today = TodayAttendance.fromJson(json);

        expect(today.hasCheckedIn, true);
        expect(today.hasCheckedOut, false);
        expect(today.checkInTime, '09:00:00');
        expect(today.checkOutTime, isNull);
      });

      test('handles fully checked out', () {
        final json = {
          'has_checked_in': true,
          'has_checked_out': true,
          'check_in_time': '09:00:00',
          'check_out_time': '17:00:00',
          'total_hours': '8.0',
          'status': 'Checked Out',
        };

        final today = TodayAttendance.fromJson(json);

        expect(today.hasCheckedIn, true);
        expect(today.hasCheckedOut, true);
        expect(today.totalHours, '8.0');
      });

      test('handles not checked in', () {
        final json = {
          'has_checked_in': false,
          'has_checked_out': false,
          'check_in_time': null,
          'check_out_time': null,
          'total_hours': null,
          'status': 'Not Checked In',
        };

        final today = TodayAttendance.fromJson(json);

        expect(today.hasCheckedIn, false);
        expect(today.status, 'Not Checked In');
      });
    });
  });

  group('OfficeSettings Model Tests', () {
    group('fromJson', () {
      test('parses office settings correctly', () {
        final json = {
          'id': 1,
          'latitude': 12.9716,
          'longitude': 77.5946,
          'radius_meters': 100,
          'office_name': 'Main Office',
          'address': '123 Business Street',
        };

        final settings = OfficeSettings.fromJson(json);

        expect(settings.id, 1);
        expect(settings.latitude, 12.9716);
        expect(settings.longitude, 77.5946);
        expect(settings.radiusMeters, 100);
        expect(settings.officeName, 'Main Office');
      });

      test('handles missing optional fields', () {
        final json = {
          'id': 2,
          'latitude': 13.0827,
          'longitude': 80.2707,
          'radius_meters': 150,
        };

        final settings = OfficeSettings.fromJson(json);

        expect(settings.id, 2);
        expect(settings.radiusMeters, 150);
        expect(settings.officeName, isNull);
        expect(settings.address, isNull);
      });
    });

    group('toJson', () {
      test('converts office settings to JSON', () {
        final settings = OfficeSettings(
          id: 1,
          latitude: 12.9716,
          longitude: 77.5946,
          radiusMeters: 100,
          officeName: 'Main Office',
          address: '123 Business Street',
        );

        final json = settings.toJson();

        expect(json['id'], 1);
        expect(json['latitude'], 12.9716);
        expect(json['longitude'], 77.5946);
        expect(json['radius_meters'], 100);
      });
    });

    group('Location validation', () {
      test('validates valid coordinates', () {
        final settings = OfficeSettings(
          id: 1,
          latitude: 12.9716,
          longitude: 77.5946,
          radiusMeters: 100,
        );

        expect(settings.latitude, greaterThan(-90));
        expect(settings.latitude, lessThan(90));
        expect(settings.longitude, greaterThan(-180));
        expect(settings.longitude, lessThan(180));
      });
    });
  });
}
