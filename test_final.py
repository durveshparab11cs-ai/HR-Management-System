#!/usr/bin/env python3
import sys
import os

# Redirect all output to a file
output_file = open('/root/test_output.log', 'w')
sys.stdout = output_file
sys.stderr = output_file

try:
    print("=" * 70)
    print("COORDINATOR API TEST")
    print("=" * 70)
    print()
    
    print("Step 1: Check import path")
    import app
    print(f"app loaded from: {app.__file__}")
    print()
    
    print("Step 2: Check coordinator routes")
    from app.blueprints.coordinator import routes as coord_routes
    print(f"coordinator.routes loaded from: {coord_routes.__file__}")
    print()
    
    print("Step 3: Check for api_search_employee")
    if hasattr(coord_routes, 'api_search_employee'):
        print("✅ api_search_employee FOUND (new version)")
    else:
        print("❌ api_search_employee NOT FOUND (old version)")
    print()
    
    print("Step 4: Create app and test endpoint")
    from app import create_app
    import json
    
    app_inst = create_app("development")
    with app_inst.test_client() as client:
        response = client.post(
            "/coordinator/api/search-employee",
            data=json.dumps({"employee_code": "E-TEST"}),
            content_type="application/json"
        )
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.content_type}")
        if response.status_code == 302:
            print(f"Location: {response.headers.get('Location')}")
            print("❌ FAILED: Still redirecting to login")
        elif response.status_code in (200, 404):
            print("✅ SUCCESS: Returning JSON response (not redirect)")
        else:
            print(f"Response preview: {response.data[:200]}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

finally:
    output_file.close()
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    
# Print the file contents
try:
    with open('/root/test_output.log', 'r') as f:
        print(f.read())
except:
    print("Could not read output file")
