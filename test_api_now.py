#!/usr/bin/env python3
"""Quick test of coordinator API"""

import urllib.request
import json

base_url = "http://localhost:8000"

print("Testing Coordinator Portal API")
print("=" * 70)

try:
    # Test search employee
    print("\nTesting: POST /coordinator/api/search-employee")
    req = urllib.request.Request(
        f"{base_url}/coordinator/api/search-employee",
        data=json.dumps({"employee_code": "E-2606026"}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    response = urllib.request.urlopen(req, timeout=5)
    status = response.status
    content_type = response.headers.get('Content-Type', '')
    body = response.read().decode('utf-8')
    
    print(f"Status: {status}")
    print(f"Content-Type: {content_type}")
    print(f"Response: {body[:200]}")
    
    if status == 200 and 'application/json' in content_type and '"success"' in body:
        print("\n✅ SUCCESS! API returns valid JSON")
    else:
        print("\n❌ FAILED: Response is not JSON or invalid status")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"Error type: {type(e)}")
