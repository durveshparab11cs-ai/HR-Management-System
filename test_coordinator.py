"""
Quick test script to verify coordinator search endpoint / models.
"""
import os
import sys

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.models.employee import Employee
from app.models.user import User
from app.extensions.database import db

app = create_app('development')

with app.app_context():
    print("\n=== Testing Coordinator Search ===\n")
    
    # 1. Check if coordinator employee exists
    coordinator = Employee.query.filter_by(employee_code="E-2606026").first()
    if coordinator:
        print(f"✓ Coordinator found: {coordinator.employee_code} - {coordinator.full_name}")
        print(f"  User ID: {coordinator.user_id}")
        print(f"  Department: {coordinator.department}")
    else:
        print("✗ Coordinator E-2606026 NOT FOUND")
    
    print("\n=== Sample Employees ===\n")
    
    # 2. List first 10 employees with their full names
    employees = Employee.query.limit(10).all()
    for e in employees:
        try:
            print(f"{e.employee_code:12s} | {e.full_name:30s} | {e.department or 'N/A'}")
        except Exception as ex:
            print(f"{e.employee_code:12s} | ERROR: {ex}")
    
    print("\n=== Test Search Query (E-2606) ===\n")
    
    # 3. Test the search logic from routes.py
    search_term = "E-2606"
    
    # Exact match
    employee = Employee.query.filter_by(employee_code=search_term).first()
    if employee:
        print(f"✓ Exact match found: {employee.employee_code} - {employee.full_name}")
    else:
        print(f"✗ No exact match for '{search_term}'")
        
        from sqlalchemy import or_
        # Try by name
        employee = Employee.query.join(User).filter(
            or_(User.first_name.ilike(f"%{search_term}%"), User.last_name.ilike(f"%{search_term}%"))
        ).first()
        
        if employee:
            print(f"✓ Name match found: {employee.employee_code} - {employee.full_name}")
        else:
            print(f"✗ No name match for '{search_term}'")
    
    print("\n=== Test Search Query (Durvesh) ===\n")
    
    search_term = "Durvesh"
    employee = Employee.query.join(User).filter(
        or_(User.first_name.ilike(f"%{search_term}%"), User.last_name.ilike(f"%{search_term}%"))
    ).first()
    
    if employee:
        print(f"✓ Name match found: {employee.employee_code} - {employee.full_name}")
    else:
        print(f"✗ No match for '{search_term}'")
    
    print("\n" + "="*60 + "\n")
