#!/usr/bin/env python
"""Debug script for testing the shift and hospital import."""

from app import create_app
from app.blueprints.admin.shift_import import ShiftImportService
from werkzeug.datastructures import FileStorage
from datetime import date
import logging

# Enable all logging
logging.basicConfig(level=logging.DEBUG, format='%(message)s')

app = create_app()
with app.app_context():
    print("=" * 80)
    print("TESTING SHIFT AND HOSPITAL IMPORT")
    print("=" * 80)
    
    # Open the test file
    with open('test_import.xlsx', 'rb') as f:
        file = FileStorage(
            stream=f,
            filename='test_import.xlsx',
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        service = ShiftImportService()
        result = service.import_from_file(
            file=file,
            effective_date=date.today().isoformat(),
            assigned_by_user_id=3
        )
        
        print("\n" + "=" * 80)
        print("IMPORT RESULT")
        print("=" * 80)
        print(f"Success: {result.get('success')}")
        print(f"Message: {result.get('message')}")
        print(f"Shifts assigned: {result.get('assigned')}")
        print(f"Hospitals assigned: {result.get('hospitals_assigned')}")
        print(f"Skipped: {result.get('skipped')}")
        print(f"Not found: {result.get('notfound')}")
        print(f"Errors: {result.get('errors')}")
        
        if result.get('details'):
            print("\nDetails:")
            for detail in result['details']:
                print(f"  {detail}")
    
    print("\n" + "=" * 80)
    print("VERIFYING DATABASE")
    print("=" * 80)
    
    from app.models.employee_shift_assignment import EmployeeShiftAssignment
    from app.models.hospital_assignment import EmployeeHospitalAssignment
    from app.models.employee import Employee
    from sqlalchemy import or_
    
    today = date.today()
    
    # Check active shift assignments
    shift_assignments = EmployeeShiftAssignment.query.filter(
        or_(
            EmployeeShiftAssignment.effective_until.is_(None),
            EmployeeShiftAssignment.effective_until >= today
        )
    ).all()
    
    print(f"\nActive shift assignments in DB: {len(shift_assignments)}")
    for sa in shift_assignments:
        emp = Employee.query.get(sa.employee_id)
        print(f"  - {emp.employee_code} ({emp.name}): {sa.shift.name if sa.shift else 'None'}")
    
    # Check active hospital assignments
    hospital_assignments = EmployeeHospitalAssignment.query.filter(
        or_(
            EmployeeHospitalAssignment.effective_until.is_(None),
            EmployeeHospitalAssignment.effective_until >= today
        )
    ).all()
    
    print(f"\nActive hospital assignments in DB: {len(hospital_assignments)}")
    for ha in hospital_assignments:
        emp = Employee.query.get(ha.employee_id)
        print(f"  - {emp.employee_code} ({emp.name}): {ha.hospital_name}")
    
    # Check ALL hospital assignments (debug)
    all_hospital_assignments = EmployeeHospitalAssignment.query.all()
    print(f"\nTOTAL hospital assignments in DB (all): {len(all_hospital_assignments)}")
