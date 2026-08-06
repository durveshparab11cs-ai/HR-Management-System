from app import create_app
from app.models.hospital_assignment import EmployeeHospitalAssignment
from app.models.employee import Employee

app = create_app()
with app.app_context():
    print("=== ALL HOSPITAL ASSIGNMENTS IN DATABASE ===\n")
    
    assignments = EmployeeHospitalAssignment.query.all()
    print(f"Total assignments: {len(assignments)}\n")
    
    for assign in assignments:
        emp = Employee.query.get(assign.employee_id)
        print(f"Employee: {emp.employee_code if emp else f'ID={assign.employee_id}'} (ID={assign.employee_id})")
        print(f"  Hospital: {assign.hospital_name}")
        print(f"  From: {assign.effective_from}")
        print(f"  Until: {assign.effective_until}")
        print()
