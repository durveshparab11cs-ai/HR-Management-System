#!/usr/bin/env python3
"""Check what employees exist in the database"""

from app import create_app
from app.models.employee_master import EmployeeMaster
from app.models.employee import Employee

app = create_app('development')
with app.app_context():
    # Check EmployeeMaster
    all_master = EmployeeMaster.query.all()
    print(f'Total in EmployeeMaster: {len(all_master)}')
    print('\nFirst 10 from EmployeeMaster:')
    for emp in all_master[:10]:
        print(f'  - {emp.employee_code}: {emp.employee_name}')
    
    # Check for specific codes
    print('\nLooking for specific codes:')
    for code in ['I-2607037', 'E-2606026', 'E-2607037', 'I-2606026']:
        emp = EmployeeMaster.query.filter_by(employee_code=code).first()
        print(f'  {code}: {"Found" if emp else "Not found"}')
