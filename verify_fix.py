#!/usr/bin/env python
"""
Test coordinator API fix - writes results to file since terminal is broken
"""
import sys
import json
import os

# Change to the app directory
os.chdir('/Users/Administrator/Documents/HRMS/smart_hrms')
sys.path.insert(0, '/Users/Administrator/Documents/HRMS/smart_hrms')

# Import and test
from app import create_app

results = []

try:
    results.append("="*70)
    results.append("COORDINATOR API FIX TEST")
    results.append("="*70)
    
    app = create_app("development")
    
    with app.test_client() as client:
        results.append("\n[TEST] POST /coordinator/api/search-employee")
        
        payload = {"employee_code": "E-2512012"}
        response = client.post(
            "/coordinator/api/search-employee",
            data=json.dumps(payload),
            content_type="application/json"
        )
        
        results.append(f"Status: {response.status_code}")
        results.append(f"Content-Type: {response.content_type}")
        
        if response.status_code == 200:
            results.append("\n✓ SUCCESS: Got 200 status (not 302 redirect!)")
            try:
                data = response.get_json()
                results.append("Response JSON:")
                results.append(json.dumps(data, indent=2))
            except Exception as e:
                results.append(f"✗ Error parsing JSON: {e}")
                results.append(f"Raw response: {response.data[:300]}")
        elif response.status_code == 302:
            results.append("\n✗ FAIL: Still getting 302 redirect")
            results.append(f"Location: {response.headers.get('Location')}")
        elif response.status_code == 404:
            results.append("\n✓ Got 404 (expected if employee not found)")
            try:
                results.append(f"Response: {response.get_json()}")
            except:
                results.append(f"Response: {response.data[:300]}")
        else:
            results.append(f"\n? Got {response.status_code}")
            results.append(f"Response: {response.data[:300]}")

except Exception as e:
    results.append(f"✗ EXCEPTION: {e}")
    import traceback
    results.append(traceback.format_exc())

# Write results to file
output = "\n".join(results)
with open('/Users/Administrator/Documents/HRMS/smart_hrms/test_results.txt', 'w') as f:
    f.write(output)

print(output)
