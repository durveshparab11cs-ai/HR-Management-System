#!/usr/bin/env python
"""Test coordinator API using Flask test client - direct approach"""
import sys
sys.path.insert(0, '/Users/Administrator/Documents/HRMS/smart_hrms')

from app import create_app
import json

print("\n" + "="*70)
print("Testing Coordinator API - Direct Flask Test Client")
print("="*70)

app = create_app("development")

with app.test_client() as client:
    # Test 1: API endpoint
    print("\n[TEST 1] POST /coordinator/api/search-employee")
    
    payload = {"employee_code": "E-2512012"}
    response = client.post(
        "/coordinator/api/search-employee",
        data=json.dumps(payload),
        content_type="application/json"
    )
    
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.content_type}")
    
    if response.status_code == 200:
        print("✓ SUCCESS: Got 200 status")
        try:
            data = response.get_json()
            print(json.dumps(data, indent=2))
        except:
            print("✗ Response is not valid JSON:")
            print(response.data[:300].decode('utf-8'))
    elif response.status_code == 302:
        print("✗ FAIL: Got 302 redirect (Flask-Login blocking)")
        print(f"Location header: {response.headers.get('Location')}")
    else:
        print(f"✗ FAIL: Got {response.status_code}")
        print(response.data[:200].decode('utf-8'))

print("\n" + "="*70)
