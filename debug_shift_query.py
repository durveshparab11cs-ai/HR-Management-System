from app import create_app
from app.models.employee import Employee
from app.models.employee_master import EmployeeMaster

app = create_app()
with app.app_context():
    # What shift_assignment.py gets
    employees = (
        Employee.query
        .filter(Employee.is_deleted == False)
        .order_by(Employee.employee_code)
        .all()
    )
    print(f"Shift Assignment query returns: {len(employees)}")
    for emp in employees:
        print(f"  - {emp.employee_code}")
    
    print(f"\nBut EmployeeMaster has: {EmployeeMaster.query.count()}")
    
    # Check if shift_assignment is using EmployeeMaster
    masters = EmployeeMaster.query.order_by(EmployeeMaster.employee_code).all()
    print(f"\nFirst 14 from EmployeeMaster:")
    for master in masters[:14]:
        print(f"  - {master.employee_code}: {master.employee_name}")
