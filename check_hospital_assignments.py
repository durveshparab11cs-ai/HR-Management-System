from app import create_app
from app.models.hospital_assignment import EmployeeHospitalAssignment
from app.models.employee import Employee

app = create_app()
with app.app_context():
    print("=== HOSPITAL ASSIGNMENTS IN DATABASE ===")
    assignments = EmployeeHospitalAssignment.query.all()
    print(f"Total hospital assignments: {len(assignments)}")
    
    for assign in assignments[:10]:
        emp = Employee.query.get(assign.employee_id)
        print(f"  - Emp: {emp.employee_code if emp else 'UNKNOWN'} ({assign.employee_id})")
        print(f"    Hospital: {assign.hospital_name}")
        print(f"    Effective From: {assign.effective_from}")
        print(f"    Effective Until: {assign.effective_until}")
        print()
