import 'package:flutter_test/flutter_test.dart';
import 'package:smart_hrms_mobile/features/dashboard/data/models/dashboard_model.dart';

void main() {
  group('EmployeeInfo Model Tests', () {
    test('fromJson parses employee info correctly', () {
      final json = {
        'employee_code': 'E-2024-001',
        'full_name': 'John Doe',
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john.doe@company.com',
        'phone': '+1-555-0123',
        'department': 'Engineering',
        'designation': 'Senior Developer',
        'branch': 'New York',
        'shift_name': 'Morning Shift',
        'date_of_joining': '2024-01-15',
        'reporting_manager': 'Jane Smith',
      };

      final employee = EmployeeInfo.fromJson(json);

      expect(employee.employeeCode, 'E-2024-001');
      expect(employee.fullName, 'John Doe');
      expect(employee.firstName, 'John');
      expect(employee.lastName, 'Doe');
      expect(employee.email, 'john.doe@company.com');
      expect(employee.phone, '+1-555-0123');
      expect(employee.department, 'Engineering');
      expect(employee.designation, 'Senior Developer');
      expect(employee.branch, 'New York');
      expect(employee.shiftName, 'Morning Shift');
      expect(employee.dateOfJoining, '2024-01-15');
      expect(employee.reportingManager, 'Jane Smith');
    });

    test('toJson converts employee info to JSON', () {
      const employee = EmployeeInfo(
        employeeCode: 'E-2024-001',
        fullName: 'John Doe',
        firstName: 'John',
        lastName: 'Doe',
        email: 'john.doe@company.com',
        phone: '+1-555-0123',
        department: 'Engineering',
        designation: 'Senior Developer',
        branch: 'New York',
        shiftName: 'Morning Shift',
        dateOfJoining: '2024-01-15',
        reportingManager: 'Jane Smith',
      );

      final json = employee.toJson();

      expect(json['employee_code'], 'E-2024-001');
      expect(json['full_name'], 'John Doe');
      expect(json['first_name'], 'John');
      expect(json['last_name'], 'Doe');
      expect(json['email'], 'john.doe@company.com');
      expect(json['phone'], '+1-555-0123');
      expect(json['department'], 'Engineering');
      expect(json['designation'], 'Senior Developer');
      expect(json['branch'], 'New York');
      expect(json['shift_name'], 'Morning Shift');
      expect(json['date_of_joining'], '2024-01-15');
      expect(json['reporting_manager'], 'Jane Smith');
    });

    test('initials getter returns correct value for two-word name', () {
      const employee = EmployeeInfo(
        employeeCode: 'E-001',
        fullName: 'John Doe',
        firstName: 'John',
        lastName: 'Doe',
        email: 'john@example.com',
        department: 'IT',
        designation: 'Developer',
      );

      expect(employee.initials, 'JD');
    });

    test('initials getter returns single letter for one-word name', () {
      const employee = EmployeeInfo(
        employeeCode: 'E-001',
        fullName: 'Madonna',
        firstName: 'Madonna',
        lastName: '',
        email: 'madonna@example.com',
        department: 'HR',
        designation: 'Manager',
      );

      expect(employee.initials, 'M');
    });

    test('initials getter handles empty name gracefully', () {
      const employee = EmployeeInfo(
        employeeCode: 'E-001',
        fullName: '',
        firstName: '',
        lastName: '',
        email: 'test@example.com',
        department: 'IT',
        designation: 'Developer',
      );

      expect(employee.initials, '?');
    });

    test('fromJson handles missing optional fields', () {
      final json = {
        'employee_code': 'E-2024-001',
        'full_name': 'John Doe',
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john.doe@company.com',
        'department': 'Engineering',
        'designation': 'Developer',
      };

      final employee = EmployeeInfo.fromJson(json);

      expect(employee.employeeCode, 'E-2024-001');
      expect(employee.fullName, 'John Doe');
      expect(employee.phone, isNull);
      expect(employee.branch, isNull);
      expect(employee.shiftName, isNull);
      expect(employee.dateOfJoining, isNull);
      expect(employee.reportingManager, isNull);
    });
  });

  group('AttendanceChartData Model Tests', () {
    test('fromJson parses attendance chart data correctly', () {
      final json = {
        'date': '2026-02-15',
        'present': 45,
        'absent': 5,
        'on_leave': 10,
      };

      final data = AttendanceChartData.fromJson(json);

      expect(data.date, '2026-02-15');
      expect(data.present, 45);
      expect(data.absent, 5);
      expect(data.onLeave, 10);
    });

    test('toJson converts attendance chart data to JSON', () {
      const data = AttendanceChartData(
        date: '2026-02-15',
        present: 45,
        absent: 5,
        onLeave: 10,
      );

      final json = data.toJson();

      expect(json['date'], '2026-02-15');
      expect(json['present'], 45);
      expect(json['absent'], 5);
      expect(json['on_leave'], 10);
    });

    test('total getter calculates correct total', () {
      const data = AttendanceChartData(
        date: '2026-02-15',
        present: 45,
        absent: 5,
        onLeave: 10,
      );

      expect(data.total, 60);
    });

    test('workPercentage getter calculates correct percentage', () {
      const data = AttendanceChartData(
        date: '2026-02-15',
        present: 45,
        absent: 5,
        onLeave: 10,
      );

      expect(data.workPercentage, closeTo(75.0, 0.1));
    });

    test('workPercentage returns 0 when total is 0', () {
      const data = AttendanceChartData(
        date: '2026-02-15',
        present: 0,
        absent: 0,
        onLeave: 0,
      );

      expect(data.workPercentage, 0);
    });

    test('fromJson handles missing fields with defaults', () {
      final json = {
        'date': '2026-02-15',
      };

      final data = AttendanceChartData.fromJson(json);

      expect(data.date, '2026-02-15');
      expect(data.present, 0);
      expect(data.absent, 0);
      expect(data.onLeave, 0);
    });
  });

  group('DashboardSummary Model Tests', () {
    test('fromJson parses dashboard summary correctly', () {
      final json = {
        'total_employees': 100,
        'present_today': 85,
        'absent_today': 10,
        'on_leave': 5,
        'late_comers': 8,
        'attendance_percentage': 85.5,
      };

      final summary = DashboardSummary.fromJson(json);

      expect(summary.totalEmployees, 100);
      expect(summary.presentToday, 85);
      expect(summary.absentToday, 10);
      expect(summary.onLeave, 5);
      expect(summary.lateComers, 8);
      expect(summary.attendancePercentage, 85.5);
    });

    test('toJson converts dashboard summary to JSON', () {
      const summary = DashboardSummary(
        totalEmployees: 100,
        presentToday: 85,
        absentToday: 10,
        onLeave: 5,
        lateComers: 8,
        attendancePercentage: 85.5,
      );

      final json = summary.toJson();

      expect(json['total_employees'], 100);
      expect(json['present_today'], 85);
      expect(json['absent_today'], 10);
      expect(json['on_leave'], 5);
      expect(json['late_comers'], 8);
      expect(json['attendance_percentage'], 85.5);
    });

    test('fromJson handles missing fields with defaults', () {
      final json = <String, dynamic>{};

      final summary = DashboardSummary.fromJson(json);

      expect(summary.totalEmployees, 0);
      expect(summary.presentToday, 0);
      expect(summary.absentToday, 0);
      expect(summary.onLeave, 0);
      expect(summary.lateComers, 0);
      expect(summary.attendancePercentage, 0.0);
    });
  });

  group('MyAttendanceStatus Model Tests', () {
    test('fromJson parses attendance status correctly', () {
      final json = {
        'check_in': '09:00 AM',
        'check_out': '05:30 PM',
        'total_hours': '8.5',
        'status': 'Present',
        'is_present': true,
        'has_checked_in': true,
        'has_checked_out': true,
      };

      final status = MyAttendanceStatus.fromJson(json);

      expect(status.checkIn, '09:00 AM');
      expect(status.checkOut, '05:30 PM');
      expect(status.totalHours, '8.5');
      expect(status.status, 'Present');
      expect(status.isPresent, true);
      expect(status.hasCheckedIn, true);
      expect(status.hasCheckedOut, true);
    });

    test('fromJson handles missing optional fields', () {
      final json = <String, dynamic>{
        'status': 'Absent',
        'is_present': false,
        'has_checked_in': false,
        'has_checked_out': false,
      };

      final status = MyAttendanceStatus.fromJson(json);

      expect(status.status, 'Absent');
      expect(status.isPresent, false);
      expect(status.hasCheckedIn, false);
      expect(status.checkIn, isNull);
      expect(status.checkOut, isNull);
      expect(status.totalHours, isNull);
    });

    test('fromJson handles missing fields with defaults', () {
      final json = <String, dynamic>{};

      final status = MyAttendanceStatus.fromJson(json);

      expect(status.status, 'Absent');
      expect(status.isPresent, false);
      expect(status.hasCheckedIn, false);
      expect(status.hasCheckedOut, false);
    });
  });

  group('LeaveBalance Model Tests', () {
    test('fromJson parses leave balance correctly', () {
      final json = {
        'leave_type': 'Sick Leave',
        'total_days': 10,
        'used_days': 2,
        'remaining_days': 8,
      };

      final balance = LeaveBalance.fromJson(json);

      expect(balance.leaveType, 'Sick Leave');
      expect(balance.totalDays, 10);
      expect(balance.usedDays, 2);
      expect(balance.remainingDays, 8);
    });

    test('fromJson handles missing fields with defaults', () {
      final json = <String, dynamic>{};

      final balance = LeaveBalance.fromJson(json);

      expect(balance.leaveType, '');
      expect(balance.totalDays, 0);
      expect(balance.usedDays, 0);
      expect(balance.remainingDays, 0);
    });

    test('fromJson parses multiple leave types correctly', () {
      final jsonList = [
        {
          'leave_type': 'Casual Leave',
          'total_days': 12,
          'used_days': 3,
          'remaining_days': 9,
        },
        {
          'leave_type': 'Paid Time Off',
          'total_days': 20,
          'used_days': 5,
          'remaining_days': 15,
        },
      ];

      final balances = jsonList.map((json) => LeaveBalance.fromJson(json)).toList();

      expect(balances, hasLength(2));
      expect(balances[0].leaveType, 'Casual Leave');
      expect(balances[1].leaveType, 'Paid Time Off');
      expect(balances[0].remainingDays, 9);
      expect(balances[1].remainingDays, 15);
    });
  });
}
