from app import create_app
from app.models.employee import Employee
from app.models.user import User

app = create_app()
with app.app_context():
    # All employees
    all_emps = Employee.query.filter(Employee.is_deleted == False).order_by(Employee.employee_code).all()
    print(f"Total employees: {len(all_emps)}\n")
    
    for emp in all_emps:
        if emp.user_id:
            user = User.query.get(emp.user_id)
            if user:
                print(f"✓ {emp.employee_code}: {user.first_name} {user.last_name} (user_id={emp.user_id})")
            else:
                print(f"✗ {emp.employee_code}: user_id={emp.user_id} BUT USER NOT FOUND!")
        else:
            print(f"✗ {emp.employee_code}: NO USER ID")
