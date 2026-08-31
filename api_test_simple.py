import requests
import json
import sys
import time

# First, check database
from app import create_app
from app.models.employee_master import EmployeeMaster

app = create_app('development')
with app.app_context():
    all_master = EmployeeMaster.query.all()
    print(f"Total employees in database: {len(all_master)}")
    if all_master:
        print("First 3 employees:")
        for emp in all_master[:3]:
            print(f"  {emp.employee_code}: {emp.employee_name}")

# Now test the API
print("\n" + "="*80)
print("TESTING API ENDPOINTS")
print("="*80)

BASE_URL = "http://localhost:8000"

# Test 1: I-code
print("\nTest 1: Searching for I-2607037")
try:
    response = requests.post(
        f"{BASE_URL}/coordinator/api/search-employee",
        json={"employee_code": "I-2607037"},
        timeout=5
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: E-code
print("\nTest 2: Searching for E-2606026")
try:
    response = requests.post(
        f"{BASE_URL}/coordinator/api/search-employee",
        json={"employee_code": "E-2606026"},
        timeout=5
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
