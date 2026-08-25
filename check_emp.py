#!/usr/bin/env python
import sys
sys.path.insert(0, '.')
from app import create_app
from app.models.employee import Employee

app = create_app()
with app.app_context():
    emp = Employee.query.filter_by(employee_code='E-2606026').first()
    if emp:
        print(f'FOUND: {emp.employee_code} | {emp.full_name} | Dept: {emp.department} | Desig: {emp.designation}')
    else:
        print('Employee E-2606026 not found!')
        print('\nFirst 3 employees in database:')
        emps = Employee.query.limit(3).all()
        for e in emps:
            print(f'  - {e.employee_code}: {e.full_name}')
