import 'package:flutter_test/flutter_test.dart';
import 'package:smart_hrms_mobile/features/payroll/data/models/payroll_model.dart';

void main() {
  group('SalarySlip Model Tests', () {
    group('fromJson', () {
      test('parses salary slip correctly', () {
        final json = {
          'id': 1,
          'employee_id': 100,
          'employee_name': 'John Doe',
          'employee_code': 'EMP001',
          'designation': 'Senior Developer',
          'department': 'IT',
          'month': 7,
          'year': 2024,
          'generated_date': '2024-07-28T10:00:00Z',
          'basic_salary': 50000.0,
          'dearness_allowance': 5000.0,
          'house_rent_allowance': 10000.0,
          'conveyance_allowance': 2000.0,
          'medical_allowance': 1500.0,
          'other_allowances': 500.0,
          'gross_salary': 69000.0,
          'professional_tax': 2500.0,
          'provident_fund': 6000.0,
          'income_tax': 8000.0,
          'other_deductions': 1000.0,
          'total_deductions': 17500.0,
          'net_salary': 51500.0,
          'days_worked': 22,
          'total_days': 30,
          'leaves_taken': 1,
          'status': 'released',
          'remarks': 'Payment processed',
          'approved_at': '2024-07-25T09:00:00Z',
          'approved_by': 'Manager Name',
          'released_at': '2024-07-27T15:00:00Z',
        };

        final slip = SalarySlip.fromJson(json);

        expect(slip.id, 1);
        expect(slip.employeeId, 100);
        expect(slip.employeeName, 'John Doe');
        expect(slip.basicSalary, 50000.0);
        expect(slip.grossSalary, 69000.0);
        expect(slip.netSalary, 51500.0);
        expect(slip.status, 'released');
      });

      test('handles missing optional fields', () {
        final json = {
          'id': 2,
          'employee_id': 101,
          'employee_name': 'Jane Smith',
          'employee_code': 'EMP002',
          'designation': 'Developer',
          'department': 'IT',
          'month': 7,
          'year': 2024,
          'generated_date': '2024-07-28T10:00:00Z',
          'basic_salary': 45000.0,
          'dearness_allowance': 4000.0,
          'house_rent_allowance': 9000.0,
          'conveyance_allowance': 1500.0,
          'medical_allowance': 1000.0,
          'other_allowances': 0.0,
          'gross_salary': 60500.0,
          'professional_tax': 2000.0,
          'provident_fund': 5400.0,
          'income_tax': 7000.0,
          'other_deductions': 0.0,
          'total_deductions': 14400.0,
          'net_salary': 46100.0,
          'days_worked': 22,
          'total_days': 30,
          'leaves_taken': 0,
          'status': 'draft',
          'remarks': null,
          'approved_at': null,
          'approved_by': null,
          'released_at': null,
        };

        final slip = SalarySlip.fromJson(json);

        expect(slip.remarks, isNull);
        expect(slip.approvedAt, isNull);
        expect(slip.approvedBy, isNull);
        expect(slip.releasedAt, isNull);
      });

      test('parses salary breakdown correctly', () {
        final json = {
          'id': 3,
          'employee_id': 102,
          'employee_name': 'Bob Wilson',
          'employee_code': 'EMP003',
          'designation': 'QA Engineer',
          'department': 'QA',
          'month': 7,
          'year': 2024,
          'generated_date': '2024-07-28T10:00:00Z',
          'basic_salary': 40000.0,
          'dearness_allowance': 3000.0,
          'house_rent_allowance': 8000.0,
          'conveyance_allowance': 1200.0,
          'medical_allowance': 800.0,
          'other_allowances': 0.0,
          'gross_salary': 53000.0,
          'professional_tax': 1500.0,
          'provident_fund': 4800.0,
          'income_tax': 5000.0,
          'other_deductions': 0.0,
          'total_deductions': 11300.0,
          'net_salary': 41700.0,
          'days_worked': 22,
          'total_days': 30,
          'leaves_taken': 0,
          'status': 'approved',
          'remarks': null,
          'approved_at': '2024-07-26T10:00:00Z',
          'approved_by': 'Manager',
          'released_at': null,
        };

        final slip = SalarySlip.fromJson(json);

        expect(slip.dearnesAllowance, 3000.0);
        expect(slip.houseRentAllowance, 8000.0);
        expect(slip.professionalTax, 1500.0);
        expect(slip.providentFund, 4800.0);
      });
    });

    group('toJson', () {
      test('converts salary slip to JSON', () {
        final slip = SalarySlip(
          id: 1,
          employeeId: 100,
          employeeName: 'John Doe',
          employeeCode: 'EMP001',
          designation: 'Senior Developer',
          department: 'IT',
          month: 7,
          year: 2024,
          generatedDate: DateTime(2024, 7, 28, 10, 0, 0),
          basicSalary: 50000.0,
          dearnesAllowance: 5000.0,
          houseRentAllowance: 10000.0,
          conveyanceAllowance: 2000.0,
          medicalAllowance: 1500.0,
          otherAllowances: 500.0,
          grossSalary: 69000.0,
          professionalTax: 2500.0,
          providentFund: 6000.0,
          incomeTax: 8000.0,
          otherDeductions: 1000.0,
          totalDeductions: 17500.0,
          netSalary: 51500.0,
          daysWorked: 22,
          totalDays: 30,
          leavesTaken: 1,
          status: 'released',
        );

        final json = slip.toJson();

        expect(json['id'], 1);
        expect(json['employee_id'], 100);
        expect(json['basic_salary'], 50000.0);
        expect(json['net_salary'], 51500.0);
      });
    });

    group('Status and calculations', () {
      test('validates draft status', () {
        final slip = SalarySlip(
          id: 1,
          employeeId: 100,
          employeeName: 'John Doe',
          employeeCode: 'EMP001',
          designation: 'Developer',
          department: 'IT',
          month: 7,
          year: 2024,
          generatedDate: DateTime(2024, 7, 28),
          basicSalary: 50000.0,
          dearnesAllowance: 5000.0,
          houseRentAllowance: 10000.0,
          conveyanceAllowance: 2000.0,
          medicalAllowance: 1500.0,
          otherAllowances: 500.0,
          grossSalary: 69000.0,
          professionalTax: 2500.0,
          providentFund: 6000.0,
          incomeTax: 8000.0,
          otherDeductions: 1000.0,
          totalDeductions: 17500.0,
          netSalary: 51500.0,
          daysWorked: 22,
          totalDays: 30,
          leavesTaken: 1,
          status: 'draft',
        );

        expect(slip.status, 'draft');
        expect(slip.statusLabel, 'Draft');
      });

      test('calculates take-home percentage', () {
        final slip = SalarySlip(
          id: 1,
          employeeId: 100,
          employeeName: 'John Doe',
          employeeCode: 'EMP001',
          designation: 'Developer',
          department: 'IT',
          month: 7,
          year: 2024,
          generatedDate: DateTime(2024, 7, 28),
          basicSalary: 50000.0,
          dearnesAllowance: 5000.0,
          houseRentAllowance: 10000.0,
          conveyanceAllowance: 2000.0,
          medicalAllowance: 1500.0,
          otherAllowances: 500.0,
          grossSalary: 100000.0,
          professionalTax: 2500.0,
          providentFund: 6000.0,
          incomeTax: 8000.0,
          otherDeductions: 1000.0,
          totalDeductions: 17500.0,
          netSalary: 75000.0,
          daysWorked: 22,
          totalDays: 30,
          leavesTaken: 0,
          status: 'approved',
        );

        final percentage = slip.takeHomePercentage;
        expect(percentage, closeTo(75.0, 0.1));
      });

      test('gets period string', () {
        final slip = SalarySlip(
          id: 1,
          employeeId: 100,
          employeeName: 'John Doe',
          employeeCode: 'EMP001',
          designation: 'Developer',
          department: 'IT',
          month: 7,
          year: 2024,
          generatedDate: DateTime(2024, 7, 28),
          basicSalary: 50000.0,
          dearnesAllowance: 5000.0,
          houseRentAllowance: 10000.0,
          conveyanceAllowance: 2000.0,
          medicalAllowance: 1500.0,
          otherAllowances: 500.0,
          grossSalary: 69000.0,
          professionalTax: 2500.0,
          providentFund: 6000.0,
          incomeTax: 8000.0,
          otherDeductions: 1000.0,
          totalDeductions: 17500.0,
          netSalary: 51500.0,
          daysWorked: 22,
          totalDays: 30,
          leavesTaken: 0,
          status: 'approved',
        );

        expect(slip.periodString, 'July 2024');
      });
    });
  });

  group('PayrollSummary Model Tests', () {
    group('fromJson', () {
      test('parses payroll summary correctly', () {
        final json = {
          'ytd_gross_salary': 500000.0,
          'ytd_net_salary': 380000.0,
          'ytd_taxes': 50000.0,
          'ytd_deductions': 120000.0,
          'paid_months': 6,
          'total_months': 12,
          'last_payment_date': '2024-07-27T10:00:00Z',
          'average_monthly_salary': 83333.0,
        };

        final summary = PayrollSummary.fromJson(json);

        expect(summary.ytdGrossSalary, 500000.0);
        expect(summary.ytdNetSalary, 380000.0);
        expect(summary.paidMonths, 6);
      });
    });
  });

  group('SalarySlipListResponse Model Tests', () {
    group('fromJson', () {
      test('parses salary slip list response', () {
        final json = {
          'items': [
            {
              'id': 1,
              'employee_id': 100,
              'employee_name': 'John Doe',
              'employee_code': 'EMP001',
              'designation': 'Developer',
              'department': 'IT',
              'month': 7,
              'year': 2024,
              'generated_date': '2024-07-28T10:00:00Z',
              'basic_salary': 50000.0,
              'dearness_allowance': 5000.0,
              'house_rent_allowance': 10000.0,
              'conveyance_allowance': 2000.0,
              'medical_allowance': 1500.0,
              'other_allowances': 500.0,
              'gross_salary': 69000.0,
              'professional_tax': 2500.0,
              'provident_fund': 6000.0,
              'income_tax': 8000.0,
              'other_deductions': 1000.0,
              'total_deductions': 17500.0,
              'net_salary': 51500.0,
              'days_worked': 22,
              'total_days': 30,
              'leaves_taken': 1,
              'status': 'released',
            }
          ],
          'total': 1,
          'page': 1,
          'per_page': 20,
          'total_pages': 1,
        };

        final response = SalarySlipListResponse.fromJson(json);

        expect(response.items.length, 1);
        expect(response.total, 1);
        expect(response.page, 1);
      });
    });
  });
}
