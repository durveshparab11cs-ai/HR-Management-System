from app import create_app
from app.blueprints.employees.repository import EmployeeRepository
from app.models.employee import Employee

app = create_app()
with app.app_context():
    repo = EmployeeRepository()
    depts = repo.get_departments()
    print(f'Departments returned: {depts}')
    
    all_emps = Employee.query.filter(Employee.is_deleted == False).all()
    print(f'\nAll employees and their departments:')
    for emp in all_emps:
        print(f'  {emp.employee_code}: dept={repr(emp.department)}')
