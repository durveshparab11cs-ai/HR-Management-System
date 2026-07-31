import 'package:flutter_test/flutter_test.dart';
import 'package:smart_hrms_mobile/features/reports/data/models/report_model.dart';

void main() {
  group('AttendanceReport Model Tests', () {
    group('fromJson', () {
      test('parses attendance report correctly', () {
        final json = {
          'employee_id': 100,
          'employee_name': 'John Doe',
          'employee_code': 'EMP001',
          'total_days': 22,
          'present_days': 20,
          'absent_days': 2,
          'half_days': 0,
          'leave_days': 0,
          'attendance_percentage': 90.9,
          'report_date': '2024-07-28',
          'department': 'IT',
          'designation': 'Senior Developer',
        };

        final report = AttendanceReport.fromJson(json);

        expect(report.employeeId, 100);
        expect(report.employeeName, 'John Doe');
        expect(report.totalDays, 22);
        expect(report.presentDays, 20);
        expect(report.attendancePercentage, 90.9);
      });

      test('handles missing optional fields', () {
        final json = {
          'employee_id': 101,
          'employee_name': 'Jane Smith',
          'employee_code': 'EMP002',
          'total_days': 20,
          'present_days': 18,
          'absent_days': 2,
          'half_days': 0,
          'leave_days': 0,
          'attendance_percentage': 90.0,
          'report_date': '2024-07-28',
          'department': null,
          'designation': null,
        };

        final report = AttendanceReport.fromJson(json);

        expect(report.department, isNull);
        expect(report.designation, isNull);
      });
    });
  });

  group('LeaveAnalytics Model Tests', () {
    group('fromJson', () {
      test('parses leave analytics correctly', () {
        final json = {
          'total_leave_balance': 20,
          'leave_used': 5,
          'leave_remaining': 15,
          'leave_type': 'Annual Leave',
          'usage_percentage': 25.0,
          'breakdown': [
            {
              'month': 'January',
              'used': 2,
              'pending': 0,
            },
            {
              'month': 'February',
              'used': 3,
              'pending': 1,
            }
          ],
        };

        final analytics = LeaveAnalytics.fromJson(json);

        expect(analytics.totalLeaveBalance, 20);
        expect(analytics.leaveUsed, 5);
        expect(analytics.leaveRemaining, 15);
        expect(analytics.leaveType, 'Annual Leave');
        expect(analytics.breakdown.length, 2);
      });

      test('handles empty breakdown', () {
        final json = {
          'total_leave_balance': 20,
          'leave_used': 0,
          'leave_remaining': 20,
          'leave_type': 'Sick Leave',
          'usage_percentage': 0.0,
          'breakdown': [],
        };

        final analytics = LeaveAnalytics.fromJson(json);

        expect(analytics.breakdown.isEmpty, true);
      });
    });
  });

  group('LeaveBreakdown Model Tests', () {
    group('fromJson', () {
      test('parses leave breakdown correctly', () {
        final json = {
          'month': 'July',
          'used': 2,
          'pending': 1,
        };

        final breakdown = LeaveBreakdown.fromJson(json);

        expect(breakdown.month, 'July');
        expect(breakdown.used, 2);
        expect(breakdown.pending, 1);
      });
    });
  });

  group('PayrollReport Model Tests', () {
    group('fromJson', () {
      test('parses payroll report correctly', () {
        final json = {
          'period': 'July 2024',
          'gross_salary': 69000.0,
          'net_salary': 51500.0,
          'total_deductions': 17500.0,
          'attendance_based_pay': 65000.0,
          'bonus': 2000.0,
          'report_date': '2024-07-28',
          'status': 'released',
          'days_worked': 22,
        };

        final report = PayrollReport.fromJson(json);

        expect(report.period, 'July 2024');
        expect(report.grossSalary, 69000.0);
        expect(report.netSalary, 51500.0);
        expect(report.status, 'released');
      });
    });
  });

  group('DashboardReportSummary Model Tests', () {
    group('fromJson', () {
      test('parses dashboard summary correctly', () {
        final json = {
          'attendance_percentage': 92.5,
          'leaves_remaining': 12,
          'ytd_earnings': 450000.0,
          'upcoming_leaves': 2,
          'current_status': 'Present',
          'last_updated': '2024-07-28T15:00:00Z',
        };

        final summary = DashboardReportSummary.fromJson(json);

        expect(summary.attendancePercentage, 92.5);
        expect(summary.leavesRemaining, 12);
        expect(summary.ytdEarnings, 450000.0);
        expect(summary.currentStatus, 'Present');
      });
    });
  });

  group('ReportFilters Model Tests', () {
    test('converts to query parameters', () {
      final filters = ReportFilters(
        startDate: DateTime(2024, 1, 1),
        endDate: DateTime(2024, 7, 31),
        department: 'IT',
        reportType: 'attendance',
        status: 'completed',
        page: 1,
        perPage: 20,
      );

      final params = filters.toQueryParams();

      expect(params['start_date'], '2024-01-01');
      expect(params['end_date'], '2024-07-31');
      expect(params['department'], 'IT');
      expect(params['report_type'], 'attendance');
      expect(params['page'], 1);
    });

    test('handles null values in filters', () {
      final filters = ReportFilters(
        page: 1,
        perPage: 20,
      );

      final params = filters.toQueryParams();

      expect(params.containsKey('start_date'), false);
      expect(params.containsKey('department'), false);
      expect(params['page'], 1);
      expect(params['per_page'], 20);
    });
  });

  group('ChartDataPoint Model Tests', () {
    group('fromJson', () {
      test('parses chart data point correctly', () {
        final json = {
          'label': 'Monday',
          'value': 8.5,
          'category': 'Hours Worked',
        };

        final dataPoint = ChartDataPoint.fromJson(json);

        expect(dataPoint.label, 'Monday');
        expect(dataPoint.value, 8.5);
        expect(dataPoint.category, 'Hours Worked');
      });

      test('handles missing category', () {
        final json = {
          'label': 'Present',
          'value': 20.0,
          'category': null,
        };

        final dataPoint = ChartDataPoint.fromJson(json);

        expect(dataPoint.category, isNull);
      });
    });
  });

  group('ReportListResponse Model Tests', () {
    test('can be instantiated with items', () {
      final response = ReportListResponse<String>(
        items: ['Report 1', 'Report 2'],
        total: 2,
        page: 1,
        perPage: 20,
        totalPages: 1,
      );

      expect(response.items.length, 2);
      expect(response.total, 2);
    });
  });
}
