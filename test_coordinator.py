<<<<<<< HEAD
#!/usr/bin/env python
import urllib.request
import json

# Test coordinator API
url = "http://localhost:8000/coordinator/api/search-employee"
payload = json.dumps({"employee_code": "E-2606026"}).encode('utf-8')

req = urllib.request.Request(
    url,
    data=payload,
    headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
    method='POST'
)

try:
    response = urllib.request.urlopen(req)
    body = response.read().decode('utf-8')
    with open('test_output.txt', 'w') as f:
        f.write(f"Status: {response.status}\n")
        f.write(f"Content-Type: {response.headers.get('Content-Type')}\n")
        f.write(f"Body (first 300 chars): {body[:300]}\n")
        f.write(f"Is JSON: {body.strip().startswith(('{', '['))}\n")
except urllib.error.HTTPError as he:
    with open('test_output.txt', 'w') as f:
        f.write(f"Error {he.code}\n")
        f.write(f"Content-Type: {he.headers.get('Content-Type')}\n")
        body = he.read().decode('utf-8')
        f.write(f"Body (first 300 chars): {body[:300]}\n")
        f.write(f"Is HTML: {'<!DOCTYPE' in body or '<html' in body.lower()}\n")
except Exception as e:
    with open('test_output.txt', 'w') as f:
        f.write(f"Exception: {type(e).__name__}: {e}\n")
=======
"""
Quick test script to verify coordinator search endpoint works.
"""
import os
os.environ['FLASK_ENV'] = 'production'
os.environ['APP_NAME'] = 'Smart HRMS'
os.environ['DATABASE_URL'] = 'sqlite:///C:/Users/Administrator/Documents/HRMS/smart_hrms/instance/smart_hrms_dev.db'

from app import create_app
from app.models.employee import Employee
from app.models.user import User
from app.extensions.database import db

app = create_app()

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
        
        # Try by name
        employee = Employee.query.join(User).filter(
            User.full_name.ilike(f"%{search_term}%")
        ).first()
        
        if employee:
            print(f"✓ Name match found: {employee.employee_code} - {employee.full_name}")
        else:
            print(f"✗ No name match for '{search_term}'")
    
    print("\n=== Test Search Query (Durvesh) ===\n")
    
    search_term = "Durvesh"
    employee = Employee.query.join(User).filter(
        User.full_name.ilike(f"%{search_term}%")
    ).first()
    
    if employee:
        print(f"✓ Name match found: {employee.employee_code} - {employee.full_name}")
    else:
        print(f"✗ No match for '{search_term}'")
    
    print("\n" + "="*60 + "\n")
>>>>>>> c1e2d4900e563df8df5d43e3f08a222543242fa3
