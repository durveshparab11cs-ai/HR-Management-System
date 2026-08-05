from app import create_app
from app.models.employee import Employee
from app.models.user import User

app = create_app()
with app.app_context():
    # Count registered employees (those with User accounts)
    registered = Employee.query.filter(Employee.is_deleted == False).count()
    
    # Count registered employees with active User accounts
    registered_with_users = (
        Employee.query
        .join(User, Employee.user_id == User.id)
        .filter(Employee.is_deleted == False)
        .count()
    )
    
    print(f"Total registered employees: {registered}")
    print(f"Registered employees with User accounts: {registered_with_users}")
    
    # List them
    emps = Employee.query.filter(Employee.is_deleted == False).all()
    print(f"\nList of all registered employees:")
    for emp in emps:
        user_info = f" -> User: {emp.user.first_name} {emp.user.last_name}" if emp.user else " -> NO USER"
        print(f"  - {emp.employee_code}: {user_info}")
