#!/usr/bin/env python
"""Diagnostic tool for hospital import issues."""

from app import create_app
from app.models.hospital_assignment import EmployeeHospitalAssignment
from app.models.employee_shift_assignment import EmployeeShiftAssignment
from app.models.employee import Employee
from app.models.hospital import Hospital
from datetime import date
from sqlalchemy import or_

app = create_app()
with app.app_context():
    today = date.today()
    
    print("\n" + "=" * 80)
    print("HR SYSTEM DIAGNOSTIC REPORT")
    print("=" * 80)
    
    # Count employees
    employees = Employee.query.filter_by(is_deleted=False).all()
    print(f"\n[1] EMPLOYEES: {len(employees)} total")
    
    for emp in employees:
        print(f"    - {emp.employee_code}: {emp.name}")
    
    # Count hospitals
    hospitals = Hospital.query.filter_by(is_active=True, is_deleted=False).all()
    print(f"\n[2] HOSPITALS: {len(hospitals)} active")
    print(f"    First 10 hospitals:")
    for h in hospitals[:10]:
        print(f"    - {h.hospital_name}")
    if len(hospitals) > 10:
        print(f"    ... and {len(hospitals) - 10} more")
    
    # Hospital assignments
    active_ha = EmployeeHospitalAssignment.query.filter(
        or_(
            EmployeeHospitalAssignment.effective_until.is_(None),
            EmployeeHospitalAssignment.effective_until >= today
        )
    ).all()
    
    print(f"\n[3] HOSPITAL ASSIGNMENTS: {len(active_ha)} active")
    for ha in active_ha:
        emp = Employee.query.get(ha.employee_id)
        print(f"    - {emp.employee_code}: {ha.hospital_name}")
    
    # Shift assignments
    active_sa = EmployeeShiftAssignment.query.filter(
        or_(
            EmployeeShiftAssignment.effective_until.is_(None),
            EmployeeShiftAssignment.effective_until >= today
        )
    ).all()
    
    print(f"\n[4] SHIFT ASSIGNMENTS: {len(active_sa)} active")
    for sa in active_sa:
        emp = Employee.query.get(sa.employee_id)
        shift = sa.shift
        print(f"    - {emp.employee_code}: {shift.name if shift else 'None'}")
    
    # Verification
    print(f"\n[5] DATA CONSISTENCY CHECK:")
    
    all_correct = True
    
    # Check hospital assignments exist for assigned employees
    for ha in active_ha:
        emp = Employee.query.get(ha.employee_id)
        hosp = Hospital.query.filter_by(hospital_name=ha.hospital_name).first()
        
        if not hosp:
            print(f"    WARNING: Hospital '{ha.hospital_name}' in assignment but not found in Hospital table")
            all_correct = False
    
    if all_correct:
        print("    OK: All hospital assignments point to valid hospitals")
    
    print(f"\n[6] UI DISPLAY TEST:")
    print(f"    When rendering shift_assignment.html:")
    print(f"    - Employees will show: {len(employees)} dropdown selects")
    print(f"    - Hospitals dropdown will show: {len(hospitals)} options")
    print(f"    - Pre-selected hospitals: {len(active_ha)}")
    
    # Expected behavior
    print(f"\n[7] EXPECTED BEHAVIOR:")
    print(f"    - Hospital selects should show:")
    for emp in employees:
        ha = EmployeeHospitalAssignment.query.filter(
            EmployeeHospitalAssignment.employee_id == emp.id,
            or_(
                EmployeeHospitalAssignment.effective_until.is_(None),
                EmployeeHospitalAssignment.effective_until >= today
            )
        ).first()
        
        if ha:
            print(f"      {emp.employee_code}: {ha.hospital_name}")
        else:
            print(f"      {emp.employee_code}: -- Select Hospital --")
    
    print("\n" + "=" * 80)
    print("END OF REPORT")
    print("=" * 80 + "\n")
