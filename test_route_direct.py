#!/usr/bin/env python
"""Test the shift_assignment route directly."""

from app import create_app
from flask import url_for

app = create_app()
with app.app_context():
    # Import the function directly
    from app.blueprints.admin.shift_assignment import assign_shifts_bulk
    
    # We can't call it directly in this context, so let's call the data gathering code manually
    from app.models.employee import Employee
    from app.models.company import Shift
    from app.models.hospital import Hospital
    from app.models.employee_shift_assignment import EmployeeShiftAssignment
    from app.models.hospital_assignment import EmployeeHospitalAssignment
    from datetime import date as date_type
    from sqlalchemy import or_
    
    today = date_type.today()
    
    employees = (
        Employee.query
        .filter(Employee.is_deleted == False)
        .order_by(Employee.employee_code)
        .all()
    )
    
    hospitals = Hospital.query.filter_by(is_active=True, is_deleted=False).order_by(Hospital.hospital_name).all()
    
    employee_hospitals = {}
    for emp in employees:
        assignment = (
            EmployeeHospitalAssignment.query
            .filter(
                EmployeeHospitalAssignment.employee_id == emp.id,
                or_(
                    EmployeeHospitalAssignment.effective_until.is_(None),
                    EmployeeHospitalAssignment.effective_until >= today
                )
            )
            .order_by(EmployeeHospitalAssignment.effective_from.desc())
            .first()
        )
        employee_hospitals[emp.id] = assignment.hospital_name if assignment else None
    
    print("=" * 80)
    print("TEMPLATE DATA")
    print("=" * 80)
    
    for emp in employees:
        hospital_name = employee_hospitals.get(emp.id)
        print(f"\nEmployee: {emp.employee_code} ({emp.name})")
        print(f"  Hospital from DB: {hospital_name}")
        print(f"  Type: {type(hospital_name)}")
        
        if hospital_name:
            # Check if it matches any hospital in the list
            matched = False
            for hosp in hospitals:
                if employee_hospitals[emp.id] == hosp.hospital_name:
                    matched = True
                    print(f"  ✓ MATCHED in hospital list: {hosp.hospital_name}")
                    break
            if not matched:
                print(f"  ✗ NOT MATCHED in hospital list")
                print(f"  Available hospitals (first 5):")
                for h in hospitals[:5]:
                    print(f"    - '{h.hospital_name}'")
