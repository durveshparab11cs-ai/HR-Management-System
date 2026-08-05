from app import create_app
from app.models.employee import Employee

app = create_app()
with app.app_context():
    # Test: get all employees (no filter)
    all_emps = Employee.query.filter(Employee.is_deleted == False).order_by(Employee.employee_code).all()
    print(f"Total employees (no filter): {len(all_emps)}")
    
    # Show departments
    from sqlalchemy import func
    depts_query = (
        app.db.session.query(func.distinct(Employee.department))
        .filter(Employee.is_deleted == False, Employee.department.isnot(None))
        .all()
    )
    print(f"\nDepartments in DB: {[d[0] for d in depts_query]}")
    
    # Test filter by department
    for emp in all_emps:
        print(f"  {emp.employee_code}: dept={repr(emp.department)}")
