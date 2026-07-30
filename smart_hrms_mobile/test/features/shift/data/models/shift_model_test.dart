import 'package:flutter_test/flutter_test.dart';
import 'package:smart_hrms_mobile/features/shift/data/models/shift_model.dart';

void main() {
  group('Shift Model Tests', () {
    group('fromJson', () {
      test('parses shift correctly', () {
        final json = {
          'id': 1,
          'name': 'Morning Shift',
          'type': 'morning',
          'start_time': '06:00',
          'end_time': '14:00',
          'description': 'Early morning shift',
          'is_active': true,
        };

        final shift = Shift.fromJson(json);

        expect(shift.id, 1);
        expect(shift.name, 'Morning Shift');
        expect(shift.type, ShiftType.morning);
        expect(shift.startTime, '06:00');
        expect(shift.endTime, '14:00');
      });

      test('handles all shift types', () {
        final types = ['morning', 'afternoon', 'evening', 'night', 'rotating'];
        final expectedTypes = [
          ShiftType.morning,
          ShiftType.afternoon,
          ShiftType.evening,
          ShiftType.night,
          ShiftType.rotating,
        ];

        for (int i = 0; i < types.length; i++) {
          final json = {
            'id': i + 1,
            'name': 'Shift ${i + 1}',
            'type': types[i],
            'start_time': '09:00',
            'end_time': '17:00',
            'is_active': true,
          };

          final shift = Shift.fromJson(json);
          expect(shift.type, expectedTypes[i]);
        }
      });

      test('handles missing optional fields', () {
        final json = {
          'id': 2,
          'name': 'Afternoon Shift',
          'type': 'afternoon',
          'start_time': '10:00',
          'end_time': '18:00',
          'is_active': true,
        };

        final shift = Shift.fromJson(json);

        expect(shift.description, isNull);
        expect(shift.isActive, true);
      });
    });

    group('toJson', () {
      test('converts shift to JSON', () {
        final shift = Shift(
          id: 1,
          name: 'Morning Shift',
          type: ShiftType.morning,
          startTime: '06:00',
          endTime: '14:00',
          description: 'Early morning shift',
          isActive: true,
        );

        final json = shift.toJson();

        expect(json['id'], 1);
        expect(json['name'], 'Morning Shift');
        expect(json['type'], 'morning');
        expect(json['start_time'], '06:00');
      });
    });

    group('ShiftType extension', () {
      test('gets correct labels', () {
        expect(ShiftType.morning.label, 'Morning Shift');
        expect(ShiftType.afternoon.label, 'Afternoon Shift');
        expect(ShiftType.evening.label, 'Evening Shift');
        expect(ShiftType.night.label, 'Night Shift');
        expect(ShiftType.rotating.label, 'Rotating Shift');
      });

      test('gets correct time ranges', () {
        expect(ShiftType.morning.timeRange, '06:00 - 14:00');
        expect(ShiftType.afternoon.timeRange, '10:00 - 18:00');
        expect(ShiftType.evening.timeRange, '14:00 - 22:00');
        expect(ShiftType.night.timeRange, '22:00 - 06:00');
        expect(ShiftType.rotating.timeRange, 'Rotating');
      });
    });
  });

  group('EmployeeShift Model Tests', () {
    group('fromJson', () {
      test('parses employee shift correctly', () {
        final json = {
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
          'effective_from': '2024-07-01',
          'effective_to': null,
          'is_current': true,
        };

        final empShift = EmployeeShift.fromJson(json);

        expect(empShift.id, 1);
        expect(empShift.employeeId, 100);
        expect(empShift.shiftId, 1);
        expect(empShift.shift.name, 'Morning Shift');
        expect(empShift.isCurrent, true);
      });

      test('handles effective_to date', () {
        final json = {
          'id': 2,
          'employee_id': 101,
          'shift_id': 2,
          'shift': {
            'id': 2,
            'name': 'Afternoon Shift',
            'type': 'afternoon',
            'start_time': '10:00',
            'end_time': '18:00',
            'is_active': true,
          },
          'effective_from': '2024-01-01',
          'effective_to': '2024-06-30',
          'is_current': false,
        };

        final empShift = EmployeeShift.fromJson(json);

        expect(empShift.effectiveTo, isNotNull);
        expect(empShift.isCurrent, false);
      });
    });

    group('toJson', () {
      test('converts employee shift to JSON', () {
        final shift = Shift(
          id: 1,
          name: 'Morning Shift',
          type: ShiftType.morning,
          startTime: '06:00',
          endTime: '14:00',
        );

        final empShift = EmployeeShift(
          id: 1,
          employeeId: 100,
          shiftId: 1,
          shift: shift,
          effectiveFrom: DateTime(2024, 7, 1),
          isCurrent: true,
        );

        final json = empShift.toJson();

        expect(json['id'], 1);
        expect(json['employee_id'], 100);
        expect(json['shift_id'], 1);
        expect(json['is_current'], true);
      });
    });
  });

  group('ShiftChangeRequest Model Tests', () {
    group('fromJson', () {
      test('parses shift change request correctly', () {
        final json = {
          'id': 1,
          'employee_id': 100,
          'employee_name': 'John Doe',
          'employee_code': 'EMP001',
          'current_shift_id': 1,
          'current_shift_name': 'Morning Shift',
          'requested_shift_id': 2,
          'requested_shift_name': 'Afternoon Shift',
          'requested_effective_from': '2024-08-01',
          'reason': 'Better for family schedule',
          'status': 'pending',
          'remarks': null,
          'created_at': '2024-07-28T10:00:00Z',
          'approved_at': null,
        };

        final request = ShiftChangeRequest.fromJson(json);

        expect(request.id, 1);
        expect(request.employeeId, 100);
        expect(request.employeeName, 'John Doe');
        expect(request.currentShiftName, 'Morning Shift');
        expect(request.requestedShiftName, 'Afternoon Shift');
        expect(request.status, 'pending');
      });

      test('handles approved shift change request', () {
        final json = {
          'id': 2,
          'employee_id': 101,
          'employee_name': 'Jane Smith',
          'employee_code': 'EMP002',
          'current_shift_id': 1,
          'current_shift_name': 'Morning Shift',
          'requested_shift_id': 3,
          'requested_shift_name': 'Evening Shift',
          'requested_effective_from': '2024-08-15',
          'reason': 'Personal reasons',
          'status': 'approved',
          'remarks': 'Approved by HR',
          'created_at': '2024-07-20T10:00:00Z',
          'approved_at': '2024-07-22T14:00:00Z',
        };

        final request = ShiftChangeRequest.fromJson(json);

        expect(request.status, 'approved');
        expect(request.remarks, 'Approved by HR');
        expect(request.approvedAt, isNotNull);
      });
    });

    group('toJson', () {
      test('converts shift change request to JSON', () {
        final request = ShiftChangeRequest(
          id: 1,
          employeeId: 100,
          employeeName: 'John Doe',
          employeeCode: 'EMP001',
          currentShiftId: 1,
          currentShiftName: 'Morning Shift',
          requestedShiftId: 2,
          requestedShiftName: 'Afternoon Shift',
          requestedEffectiveFrom: DateTime(2024, 8, 1),
          reason: 'Better for family schedule',
          status: 'pending',
          createdAt: DateTime(2024, 7, 28, 10, 0, 0),
        );

        final json = request.toJson();

        expect(json['id'], 1);
        expect(json['employee_id'], 100);
        expect(json['current_shift_id'], 1);
        expect(json['requested_shift_id'], 2);
      });
    });

    group('Status validation', () {
      test('validates pending status', () {
        final request = ShiftChangeRequest(
          id: 1,
          employeeId: 100,
          employeeName: 'John Doe',
          employeeCode: 'EMP001',
          currentShiftId: 1,
          currentShiftName: 'Morning Shift',
          requestedShiftId: 2,
          requestedShiftName: 'Afternoon Shift',
          requestedEffectiveFrom: DateTime(2024, 8, 1),
          reason: 'Better for family schedule',
          status: 'pending',
          createdAt: DateTime(2024, 7, 28),
        );

        expect(request.status, 'pending');
      });

      test('validates approved status', () {
        final request = ShiftChangeRequest(
          id: 1,
          employeeId: 100,
          employeeName: 'John Doe',
          employeeCode: 'EMP001',
          currentShiftId: 1,
          currentShiftName: 'Morning Shift',
          requestedShiftId: 2,
          requestedShiftName: 'Afternoon Shift',
          requestedEffectiveFrom: DateTime(2024, 8, 1),
          reason: 'Better for family schedule',
          status: 'approved',
          createdAt: DateTime(2024, 7, 28),
        );

        expect(request.status, 'approved');
      });
    });
  });

  group('ShiftChangeRequestListResponse Model Tests', () {
    group('fromJson', () {
      test('parses list response correctly', () {
        final json = {
          'items': [
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
              'reason': 'Better for family schedule',
              'status': 'pending',
              'created_at': '2024-07-28T10:00:00Z',
            }
          ],
          'total': 1,
          'page': 1,
          'per_page': 20,
          'total_pages': 1,
        };

        final response = ShiftChangeRequestListResponse.fromJson(json);

        expect(response.items.length, 1);
        expect(response.total, 1);
      });
    });
  });
}
