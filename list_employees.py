#!/usr/bin/env python3
"""List all employees to find Durvesh"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models.employee import Employee

app = create_app("production")

with app.app_context():
    print("All Employees:")
    print("="*80)
    
    employees = Employee.query.limit(20).all()
    
    for emp in employees:
        print(f"ID={emp.id:3} | Code={emp.employee_code:15} | Name={emp.full_name:30} | User ID={emp.user_id}")
    
    print(f"\nTotal employees: {Employee.query.count()}")
    
    # Search for Durvesh variants
    print("\n" + "="*80)
    print("Searching for 'Durvesh'...")
    durvesh_variants = Employee.query.filter(
        Employee.full_name.ilike('%durvesh%')
    ).all()
    
    if durvesh_variants:
        print(f"Found {len(durvesh_variants)}:")
        for emp in durvesh_variants:
            print(f"  ID={emp.id}, Code={emp.employee_code}, Name={emp.full_name}")
    else:
        print("No employees with 'Durvesh' in name found")
