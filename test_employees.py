from app import create_app
from app.blueprints.employees.repository import EmployeeRepository

app = create_app()
with app.app_context():
    repo = EmployeeRepository()
    result = repo.get_all(page=1, per_page=25)
    print(f"Total employees found: {result.total}")
    for emp in result.items:
        source = emp.get('source', 'unknown')
        name = f"{emp['first_name']} {emp['last_name']}"
        code = emp['employee_code']
        print(f"  - {code}: {name} (from {source})")
