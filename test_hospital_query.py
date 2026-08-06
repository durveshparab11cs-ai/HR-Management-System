from app import create_app
from app.models.hospital_assignment import EmployeeHospitalAssignment
from app.models.employee import Employee
from datetime import date
from sqlalchemy import or_

app = create_app()
with app.app_context():
    print("=== TESTING HOSPITAL ASSIGNMENT QUERY ===\n")
    
    employees = Employee.query.filter(Employee.is_deleted == False).all()[:3]
    
    for emp in employees:
        today = date.today()
        
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
        
        hospital_name = assignment.hospital_name if assignment else None
        
        print(f"Employee: {emp.employee_code} (ID={emp.id})")
        print(f"  Hospital Assignment found: {assignment is not None}")
        if assignment:
            print(f"  Hospital: {assignment.hospital_name}")
            print(f"  From: {assignment.effective_from}")
            print(f"  Until: {assignment.effective_until}")
        else:
            print(f"  Hospital: None")
        print()
