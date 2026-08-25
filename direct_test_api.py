#!/usr/bin/env python3
"""Direct test of coordinator API by importing the app"""

import sys
import os

# Add current dir to path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.extensions.database import db

# Create app
app = create_app("development")

with app.app_context():
    # Check if Employee E-2606026 exists
    from app.models.employee import Employee
    
    emp = Employee.query.filter_by(employee_code="E-2606026").first()
    
    if emp:
        print(f"✓ Found employee: {emp.full_name}")
        print(f"  Code: {emp.employee_code}")
        print(f"  Department: {emp.department}")
        print(f"  Designation: {emp.designation}")
        print(f"  Email: {emp.email}")
    else:
        print("✗ Employee E-2606026 not found")
        # Try listing employees
        emps = Employee.query.limit(5).all()
        if emps:
            print(f"\nFirst {len(emps)} employees:")
            for e in emps:
                print(f"  - {e.employee_code}: {e.full_name}")
        else:
            print("✗ No employees in database")

    # Test API endpoint directly
    print("\n" + "="*70)
    print("Testing API endpoint directly")
    print("="*70)
    
    with app.test_client() as client:
        # Test 1: Search employee
        resp = client.post('/coordinator/api/search-employee',
            json={"employee_code": "E-2606026"},
            content_type='application/json'
        )
        
        print(f"\nStatus: {resp.status_code}")
        print(f"Content-Type: {resp.content_type}")
        print(f"Data: {resp.get_json()}")
        
        if resp.status_code == 200 and resp.content_type == 'application/json':
            print("✓ API returns valid JSON")
        else:
            print("✗ API response issue")
