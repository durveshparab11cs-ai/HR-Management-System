from app import create_app
from app.blueprints.employees.repository import EmployeeRepository

app = create_app()
with app.app_context():
    repo = EmployeeRepository()
    result = repo.get_all(page=1, per_page=25)
    print(f"get_all() returned: {result.total} employees\n")
    for i, emp in enumerate(result.items, 1):
        name = f"{emp.user.first_name} {emp.user.last_name}"
        code = emp.employee_code
        print(f"{i}. {code}: {name}")
