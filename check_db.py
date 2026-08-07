#!/usr/bin/env python
"""Check what's in the database."""

from app import create_app
from app.models.hospital_assignment import EmployeeHospitalAssignment
from app.models.employee_shift_assignment import EmployeeShiftAssignment
from app.models.employee import Employee
from datetime import date
from sqlalchemy import or_

app = create_app()
with app.app_context():
    today = date.today()
    
    print("=" * 80)
    print("HOSPITAL ASSIGNMENTS")
    print("=" * 80)
    
    # Check ACTIVE hospital assignments
    active = EmployeeHospitalAssignment.query.filter(
        or_(
            EmployeeHospitalAssignment.effective_until.is_(None),
            EmployeeHospitalAssignment.effective_until >= today
        )
    ).all()
    
    print(f"Active hospital assignments: {len(active)}")
    for ha in active:
        emp = Employee.query.get(ha.employee_id)
        if emp and emp.employee_code in ['E-2512012', 'E-2603025', 'E-2606026']:
            print(f"  {emp.employee_code}: {ha.hospital_name}")
    
    # Check ACTIVE shift assignments
    active_shifts = EmployeeShiftAssignment.query.filter(
        or_(
            EmployeeShiftAssignment.effective_until.is_(None),
            EmployeeShiftAssignment.effective_until >= today
        )
    ).all()
    
    print(f"\nActive shift assignments: {len(active_shifts)}")
    for sa in active_shifts:
        emp = Employee.query.get(sa.employee_id)
        if emp and emp.employee_code in ['E-2512012', 'E-2603025', 'E-2606026']:
            shift = sa.shift
            print(f"  {emp.employee_code}: {shift.name if shift else 'None'}")
    
    # Check the 3 specific employees
    print("\n" + "=" * 80)
    print("SPECIFIC EMPLOYEES")
    print("=" * 80)
    
    for emp_code in ['E-2512012', 'E-2603025', 'E-2606026']:
        emp = Employee.query.filter_by(employee_code=emp_code).first()
        if emp:
            ha = EmployeeHospitalAssignment.query.filter(
                EmployeeHospitalAssignment.employee_id == emp.id,
                or_(
                    EmployeeHospitalAssignment.effective_until.is_(None),
                    EmployeeHospitalAssignment.effective_until >= today
                )
            ).first()
            
            sa = EmployeeShiftAssignment.query.filter(
                EmployeeShiftAssignment.employee_id == emp.id,
                or_(
                    EmployeeShiftAssignment.effective_until.is_(None),
                    EmployeeShiftAssignment.effective_until >= today
                )
            ).first()
            
            print(f"{emp_code}:")
            print(f"  Hospital: {ha.hospital_name if ha else 'None'}")
            print(f"  Shift: {sa.shift.name if sa and sa.shift else 'None'}")
