import 'package:flutter_test/flutter_test.dart';
import 'package:smart_hrms_mobile/features/leave/data/models/leave_model.dart';

void main() {
  group('LeaveType Model Tests', () {
    group('fromJson', () {
      test('parses leave type correctly', () {
        final json = {
          'id': 1,
          'name': 'Annual Leave',
          'code': 'AL',
          'max_days': 20,
          'requires_approval': true,
          'description': 'Annual paid leave',
        };

        final leaveType = LeaveType.fromJson(json);

        expect(leaveType.id, 1);
        expect(leaveType.name, 'Annual Leave');
        expect(leaveType.code, 'AL');
        expect(leaveType.maxDays, 20);
        expect(leaveType.requiresApproval, true);
      });

      test('handles missing optional fields', () {
        final json = {
          'id': 2,
          'name': 'Sick Leave',
          'code': 'SL',
          'max_days': 10,
          'requires_approval': false,
        };

        final leaveType = LeaveType.fromJson(json);

        expect(leaveType.description, isNull);
      });
    });
  });

  group('LeaveRequest Model Tests', () {
    group('fromJson', () {
      test('parses leave request correctly', () {
        final json = {
          'id': 1,
          'employee_id': 100,
          'employee_name': 'John Doe',
          'employee_code': 'EMP001',
          'leave_type_id': 1,
          'leave_type_name': 'Annual Leave',
          'start_date': '2024-08-01',
          'end_date': '2024-08-05',
          'total_days': 5,
          'reason': 'Family visit',
          'status': 'pending',
          'approver_id': 50,
          'approver_name': 'Manager Name',
          'approver_remarks': null,
          'approved_at': null,
          'created_at': '2024-07-28T10:00:00Z',
          'is_half_day': false,
          'is_early_leave': false,
        };

        final request = LeaveRequest.fromJson(json);

        expect(request.id, 1);
        expect(request.employeeId, 100);
        expect(request.employeeName, 'John Doe');
        expect(request.leaveTypeId, 1);
        expect(request.leaveTypeName, 'Annual Leave');
        expect(request.totalDays, 5);
        expect(request.reason, 'Family visit');
        expect(request.status, 'pending');
      });

      test('handles half day leave', () {
        final json = {
          'id': 2,
          'employee_id': 101,
          'employee_name': 'Jane Smith',
          'employee_code': 'EMP002',
          'leave_type_id': 1,
          'leave_type_name': 'Annual Leave',
          'start_date': '2024-08-01',
          'end_date': '2024-08-01',
          'total_days': 1,
          'reason': 'Doctor appointment',
          'status': 'approved',
          'approver_id': 50,
          'approver_name': 'Manager Name',
          'approver_remarks': 'Approved',
          'approved_at': '2024-07-28T11:00:00Z',
          'created_at': '2024-07-28T10:00:00Z',
          'is_half_day': true,
          'is_early_leave': false,
        };

        final request = LeaveRequest.fromJson(json);

        expect(request.isHalfDay, true);
        expect(request.status, 'approved');
        expect(request.approverRemarks, 'Approved');
      });

      test('handles null optional approver fields', () {
        final json = {
          'id': 3,
          'employee_id': 102,
          'employee_name': 'Bob Wilson',
          'employee_code': null,
          'leave_type_id': 2,
          'leave_type_name': 'Sick Leave',
          'start_date': '2024-08-02',
          'end_date': '2024-08-02',
          'total_days': 1,
          'reason': 'Not feeling well',
          'status': 'pending',
          'approver_id': null,
          'approver_name': null,
          'approver_remarks': null,
          'approved_at': null,
          'created_at': '2024-07-29T09:00:00Z',
          'is_half_day': false,
          'is_early_leave': false,
        };

        final request = LeaveRequest.fromJson(json);

        expect(request.approverId, isNull);
        expect(request.approverName, isNull);
        expect(request.employeeCode, isNull);
      });
    });

    group('toJson', () {
      test('converts leave request to JSON', () {
        final request = LeaveRequest(
          id: 1,
          employeeId: 100,
          employeeName: 'John Doe',
          employeeCode: 'EMP001',
          leaveTypeId: 1,
          leaveTypeName: 'Annual Leave',
          startDate: DateTime(2024, 8, 1),
          endDate: DateTime(2024, 8, 5),
          totalDays: 5,
          reason: 'Family visit',
          status: 'pending',
          approverId: 50,
          approverName: 'Manager Name',
          createdAt: DateTime(2024, 7, 28, 10, 0, 0),
          isHalfDay: false,
          isEarlyLeave: false,
        );

        final json = request.toJson();

        expect(json['id'], 1);
        expect(json['employee_id'], 100);
        expect(json['employee_name'], 'John Doe');
        expect(json['leave_type_id'], 1);
        expect(json['total_days'], 5);
        expect(json['reason'], 'Family visit');
      });
    });

    group('Status validation', () {
      test('validates pending status', () {
        final request = LeaveRequest(
          id: 1,
          employeeId: 100,
          employeeName: 'John Doe',
          leaveTypeId: 1,
          leaveTypeName: 'Annual Leave',
          startDate: DateTime(2024, 8, 1),
          endDate: DateTime(2024, 8, 5),
          totalDays: 5,
          reason: 'Family visit',
          status: 'pending',
          createdAt: DateTime(2024, 7, 28),
          isHalfDay: false,
          isEarlyLeave: false,
        );

        expect(request.status, 'pending');
      });

      test('validates approved status', () {
        final request = LeaveRequest(
          id: 2,
          employeeId: 101,
          employeeName: 'Jane Smith',
          leaveTypeId: 1,
          leaveTypeName: 'Annual Leave',
          startDate: DateTime(2024, 8, 1),
          endDate: DateTime(2024, 8, 5),
          totalDays: 5,
          reason: 'Family visit',
          status: 'approved',
          createdAt: DateTime(2024, 7, 28),
          isHalfDay: false,
          isEarlyLeave: false,
        );

        expect(request.status, 'approved');
      });

      test('validates rejected status', () {
        final request = LeaveRequest(
          id: 3,
          employeeId: 102,
          employeeName: 'Bob Wilson',
          leaveTypeId: 1,
          leaveTypeName: 'Annual Leave',
          startDate: DateTime(2024, 8, 1),
          endDate: DateTime(2024, 8, 5),
          totalDays: 5,
          reason: 'Family visit',
          status: 'rejected',
          createdAt: DateTime(2024, 7, 28),
          isHalfDay: false,
          isEarlyLeave: false,
        );

        expect(request.status, 'rejected');
      });
    });
  });

  group('LeaveBalance Model Tests', () {
    group('fromJson', () {
      test('parses leave balance correctly', () {
        final json = {
          'leave_type_id': 1,
          'leave_type_name': 'Annual Leave',
          'total_days': 20,
          'used_days': 5,
          'remaining_days': 15,
        };

        final balance = LeaveBalance.fromJson(json);

        expect(balance.leaveTypeId, 1);
        expect(balance.leaveTypeName, 'Annual Leave');
        expect(balance.totalDays, 20);
        expect(balance.usedDays, 5);
        expect(balance.remainingDays, 15);
      });
    });
  });

  group('Manager Model Tests', () {
    group('fromJson', () {
      test('parses manager correctly', () {
        final json = {
          'id': 50,
          'name': 'Manager Name',
          'employee_code': 'MGR001',
          'department': 'HR',
        };

        final manager = Manager.fromJson(json);

        expect(manager.id, 50);
        expect(manager.name, 'Manager Name');
        expect(manager.employeeCode, 'MGR001');
        expect(manager.department, 'HR');
      });

      test('handles null department', () {
        final json = {
          'id': 51,
          'name': 'Another Manager',
          'employee_code': 'MGR002',
          'department': null,
        };

        final manager = Manager.fromJson(json);

        expect(manager.department, isNull);
      });
    });
  });
}
