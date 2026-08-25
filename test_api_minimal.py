#!/usr/bin/env python3
"""Minimal test of coordinator API"""
import json
import sys
import time

# Use urllib instead of requests (no external dependencies)
from urllib.request import Request, urlopen
from urllib.error import URLError

BASE_URL = "http://localhost:8000"
ENDPOINT = "/coordinator/api/search-employee"

payload = {"employee_code": "E-2512012"}
payload_json = json.dumps(payload).encode('utf-8')

print("=" * 70)
print("TESTING COORDINATOR API")
print("=" * 70)
print(f"\nRequest: POST {BASE_URL}{ENDPOINT}")
print(f"Body: {payload}")
print()

try:
    # Create request
    req = Request(
        f"{BASE_URL}{ENDPOINT}",
        data=payload_json,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    # Make request
    with urlopen(req) as response:
        status = response.status
        content_type = response.headers.get('Content-Type', 'N/A')
        body = response.read().decode('utf-8')
        
        print(f"✅ Response:")
        print(f"   Status: {status}")
        print(f"   Content-Type: {content_type}")
        print(f"   Body: {body[:200]}")
        print()
        
        # Parse JSON
        try:
            data = json.loads(body)
            print(f"✅ SUCCESS: Response is JSON (not 302 HTML)")
            print(f"   Success: {data.get('success')}")
            if data.get('employee'):
                print(f"   Employee: {data['employee'].get('full_name')} ({data['employee'].get('employee_code')})")
            sys.exit(0)
        except json.JSONDecodeError:
            print(f"❌ Response is not JSON")
            sys.exit(1)
            
except URLError as e:
    print(f"❌ Request failed: {e}")
    if hasattr(e, 'code'):
        print(f"   Status Code: {e.code}")
        try:
            error_body = e.read().decode('utf-8')
            print(f"   Body: {error_body[:200]}")
        except:
            pass
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)
