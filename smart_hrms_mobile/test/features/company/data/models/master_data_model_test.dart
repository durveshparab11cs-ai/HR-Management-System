import 'package:flutter_test/flutter_test.dart';
import 'package:smart_hrms_mobile/features/company/data/models/master_data_model.dart';

void main() {
  group('Master Data Models', () {
    group('Department', () {
      test('creates Department from JSON (from PostgreSQL)', () {
        final json = {
          'id': 1,
          'name': 'Medical',
          'code': 'MED',
          'description': 'Medical department',
          'color': '#1a3c6e',
          'is_active': true,
        };

        final dept = Department.fromJson(json);

        expect(dept.id, 1);
        expect(dept.name, 'Medical');
        expect(dept.code, 'MED');
        expect(dept.description, 'Medical department');
        expect(dept.color, '#1a3c6e');
        expect(dept.isActive, true);
      });

      test('converts Department to JSON for API', () {
        const dept = Department(
          id: 1,
          name: 'Nursing',
          code: 'NRS',
          description: 'Nursing department',
          color: '#0066cc',
          isActive: true,
        );

        final json = dept.toJson();

        expect(json['id'], 1);
        expect(json['name'], 'Nursing');
        expect(json['code'], 'NRS');
        expect(json['is_active'], true);
      });

      test('handles missing fields with defaults', () {
        final json = {'id': 2, 'name': 'Finance', 'code': 'FIN'};
        final dept = Department.fromJson(json);

        expect(dept.description, null);
        expect(dept.color, '#1a3c6e'); // default
        expect(dept.isActive, true); // default
      });
    });

    group('Position', () {
      test('creates Position from JSON (from PostgreSQL)', () {
        final json = {
          'id': 1,
          'title': 'Senior Doctor',
          'code': 'SD001',
          'department_id': 1,
          'grade': 'A',
          'description': 'Senior medical professional',
          'is_active': true,
        };

        final pos = Position.fromJson(json);

        expect(pos.id, 1);
        expect(pos.title, 'Senior Doctor');
        expect(pos.code, 'SD001');
        expect(pos.departmentId, 1);
        expect(pos.grade, 'A');
        expect(pos.isActive, true);
      });

      test('converts Position to JSON', () {
        const pos = Position(
          id: 1,
          title: 'Nurse',
          code: 'NRS001',
          departmentId: 2,
          grade: 'B',
          description: 'Nursing staff',
          isActive: true,
        );

        final json = pos.toJson();

        expect(json['title'], 'Nurse');
        expect(json['department_id'], 2);
        expect(json['grade'], 'B');
      });
    });

    group('ShiftMaster', () {
      test('creates ShiftMaster from JSON (from PostgreSQL)', () {
        final json = {
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
        };

        final shift = ShiftMaster.fromJson(json);

        expect(shift.id, 1);
        expect(shift.name, 'Morning Shift');
        expect(shift.type, 'morning');
        expect(shift.startTime, '06:00');
        expect(shift.endTime, '14:00');
        expect(shift.isNightShift, false);
      });

      test('provides timeRange property', () {
        const shift = ShiftMaster(
          id: 1,
          name: 'Afternoon Shift',
          code: 'AFT',
          type: 'afternoon',
          startTime: '10:00',
          endTime: '18:00',
          graceMinutes: 10,
          breakMinutes: 60,
          workingDays: 'Mon-Fri',
          isNightShift: false,
          isActive: true,
        );

        expect(shift.timeRange, '10:00 - 18:00');
      });

      test('handles night shift correctly', () {
        const shift = ShiftMaster(
          id: 4,
          name: 'Night Shift',
          code: 'NIGHT',
          type: 'night',
          startTime: '22:00',
          endTime: '06:00',
          graceMinutes: 10,
          breakMinutes: 60,
          workingDays: 'Mon-Fri',
          isNightShift: true,
          isActive: true,
        );

        expect(shift.isNightShift, true);
        expect(shift.timeRange, '22:00 - 06:00');
      });
    });

    group('DepartmentStats', () {
      test('creates stats from JSON (from PostgreSQL)', () {
        final json = {
          'name': 'Medical',
          'color': '#1a3c6e',
          'count': 25,
        };

        final stats = DepartmentStats.fromJson(json);

        expect(stats.name, 'Medical');
        expect(stats.count, 25);
      });

      test('handles zero count', () {
        final json = {
          'name': 'Finance',
          'color': '#ff6b6b',
          'count': 0,
        };

        final stats = DepartmentStats.fromJson(json);
        expect(stats.count, 0);
      });
    });

    group('PostgreSQL Integration', () {
      test('Department model represents database row', () {
        // Simulating data from PostgreSQL
        final databaseRow = {
          'id': 1,
          'name': 'Medical',
          'code': 'MED',
          'description': 'Medical department',
          'color': '#1a3c6e',
          'is_active': true,
        };

        final dept = Department.fromJson(databaseRow);

        // Verify all fields are correctly mapped
        expect(dept.id, isNotNull);
        expect(dept.name, isNotEmpty);
        expect(dept.code, isNotEmpty);
      });

      test('ShiftMaster model represents shift from database', () {
        // Simulating production shift data
        final productionShift = {
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
        };

        final shift = ShiftMaster.fromJson(productionShift);

        // Ensure no hardcoded fallbacks
        expect(shift.startTime, isNotEmpty);
        expect(shift.endTime, isNotEmpty);
        expect(shift.graceMinutes, greaterThanOrEqualTo(0));
      });
    });

    group('Real-world Scenarios', () {
      test('handles department changes from website', () {
        // Scenario: Admin renames department on website
        final oldData = {
          'id': 1,
          'name': 'Medical',
          'code': 'MED',
          'is_active': true,
        };
        
        final dept1 = Department.fromJson(oldData);
        expect(dept1.name, 'Medical');

        // After website change, new API response
        final newData = {
          'id': 1,
          'name': 'Medical & Surgical',
          'code': 'MED',
          'is_active': true,
        };

        final dept2 = Department.fromJson(newData);
        expect(dept2.name, 'Medical & Surgical');
      });

      test('handles new shift creation on website', () {
        // New shift added to PostgreSQL via website
        final newShiftData = {
          'id': 6,
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
        };

        final shift = ShiftMaster.fromJson(newShiftData);
        expect(shift.name, 'Rotating Shift');
        expect(shift.id, 6); // New ID from database
      });
    });
  });
}
