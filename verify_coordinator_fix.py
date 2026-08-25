#!/usr/bin/env python
"""Verify that coordinator API returns JSON, not HTML redirect."""
import sys
import json
sys.path.insert(0, '.')

from app import create_app

app = create_app()

# Test 1: Check if employee E-2606026 exists in database
print("=" * 60)
print("TEST 1: Check if employee E-2606026 exists in database")
print("=" * 60)

with app.app_context():
    from app.models.employee import Employee
    emp = Employee.query.filter_by(employee_code='E-2606026').first()
    if emp:
        print(f"✓ FOUND: {emp.employee_code} | {emp.full_name}")
        print(f"  Department: {emp.department}")
        print(f"  Designation: {emp.designation}")
    else:
        print(f"✗ NOT FOUND: E-2606026")
        print("\nListing first 5 employees:")
        emps = Employee.query.limit(5).all()
        for e in emps:
            print(f"  - {e.employee_code}: {e.full_name}")

# Test 2: Test API endpoint using test client
print("\n" + "=" * 60)
print("TEST 2: Call coordinator API endpoint")
print("=" * 60)

with app.test_client() as client:
    response = client.post(
        '/coordinator/api/search-employee',
        json={"employee_code": "E-2606026"},
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    
    # Try to parse response
    try:
        data = response.get_json()
        print(f"\n✓ SUCCESS: Response is valid JSON")
        print(f"Response:\n{json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"\n✗ FAILED: Cannot parse JSON")
        print(f"Error: {e}")
        print(f"\nResponse text (first 500 chars):\n{response.get_data(as_text=True)[:500]}")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)
