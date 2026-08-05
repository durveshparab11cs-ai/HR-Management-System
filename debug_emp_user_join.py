from app import create_app
from app.models.employee import Employee
from app.models.user import User

app = create_app()
with app.app_context():
    # All employees (no join)
    all_emps = Employee.query.filter(Employee.is_deleted == False).all()
    print(f"Total employees in Employee table: {len(all_emps)}")
    for emp in all_emps:
        has_user = "YES" if emp.user_id else "NO"
        print(f"  {emp.employee_code}: user_id={emp.user_id} ({has_user})")
    
    print("\n" + "="*60 + "\n")
    
    # Employees with User join
    emp_with_users = (
        Employee.query
        .join(User, Employee.user_id == User.id)
        .filter(Employee.is_deleted == False)
        .all()
    )
    print(f"Employees WITH User join: {len(emp_with_users)}")
    for emp in emp_with_users:
        print(f"  {emp.employee_code}: {emp.user.first_name} {emp.user.last_name}")
