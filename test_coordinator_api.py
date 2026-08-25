#!/usr/bin/env python
"""
Direct test of coordinator API by calling Flask app directly.
This bypasses networking and shows exactly what the endpoints return.
"""

import sys
import json
from app import create_app

def test_api():
    print("\n" + "=" * 80)
    print("COORDINATOR API DIRECT TEST")
    print("=" * 80 + "\n")
    
    # Create Flask app
    app = create_app("development")
    
    # Create test client
    client = app.test_client()
    
    print("1. Testing GET /coordinator/portal\n")
    print("-" * 80)
    response = client.get("/coordinator/portal")
    print(f"   Status: {response.status_code}")
    print(f"   Content-Type: {response.content_type}")
    print(f"   Length: {len(response.data)} bytes")
    if response.status_code == 200:
        print("   ✅ Portal page loaded (HTML)")
    else:
        print(f"   ❌ Failed: {response.status_code}")
    print()
    
    print("2. Testing POST /coordinator/api/search-employee\n")
    print("-" * 80)
    
    # Test search-employee
    search_payload = {
        "employee_code": "E-2606026"
    }
    
    print(f"   Request: POST /coordinator/api/search-employee")
    print(f"   Body: {json.dumps(search_payload, indent=2)}")
    print()
    
    response = client.post(
        "/coordinator/api/search-employee",
        json=search_payload,
        content_type="application/json"
    )
    
    print(f"   Status: {response.status_code}")
    print(f"   Content-Type: {response.content_type}")
    print(f"   Raw Response: {response.data[:200]}")
    print()
    
    try:
        data = response.get_json()
        print(f"   Parsed JSON:")
        print(json.dumps(data, indent=2))
        if data.get("success"):
            print("   ✅ API returned JSON with success=True")
        else:
            print(f"   ⚠️  API returned JSON with success=False")
            print(f"   Error: {data.get('error')}")
    except Exception as e:
        print(f"   ❌ Failed to parse JSON: {e}")
        print(f"   Response body: {response.data.decode('utf-8', errors='replace')[:500]}")
    
    print()
    print("3. Testing POST /coordinator/api/get-gps\n")
    print("-" * 80)
    
    response = client.post("/coordinator/api/get-gps")
    print(f"   Status: {response.status_code}")
    print(f"   Content-Type: {response.content_type}")
    
    try:
        data = response.get_json()
        print(f"   Response:")
        print(json.dumps(data, indent=2))
        if data.get("success"):
            print("   ✅ API returned JSON")
        else:
            print(f"   ❌ API returned error")
    except Exception as e:
        print(f"   ❌ Failed to parse JSON: {e}")
    
    print()
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    test_api()
