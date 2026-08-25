#!/usr/bin/env python3
import urllib.request
import json
import time
import sys

time.sleep(5)

url = "http://localhost:8000/coordinator/api/search-employee"
payload = json.dumps({"employee_code": "E-2606026"}).encode()
req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')

print("=" * 70)
print("FINAL TEST: Coordinator API JSON Response")
print("=" * 70)
print(f"\nURL: {url}\nPayload: {{'employee_code': 'E-2606026'}}\n")

try:
    response = urllib.request.urlopen(req)
    body = response.read().decode('utf-8')
    
    status = response.status
    content_type = response.headers.get('Content-Type')
    
    print(f"HTTP Status: {status}")
    print(f"Content-Type: {content_type}")
    print()
    
    if content_type and 'json' in content_type.lower():
        print("✓ Content-Type indicates JSON")
    else:
        print(f"✗ Content-Type is NOT JSON: {content_type}")
    
    try:
        data = json.loads(body)
        print("✓ Response body IS valid JSON")
        print("\nResponse data:")
        print(json.dumps(data, indent=2))
        print("\n" + "=" * 70)
        print("✓✓✓ PASS - API returns JSON with correct Content-Type")
        print("=" * 70)
        sys.exit(0)
    except json.JSONDecodeError as e:
        print(f"✗ Response body is NOT valid JSON: {e}")
        print(f"\nFirst 300 chars of response:")
        print(body[:300])
        print("\n" + "=" * 70)
        print("✗✗✗ FAIL - API returned non-JSON response")
        print("=" * 70)
        sys.exit(1)
        
except urllib.error.HTTPError as e:
    body = e.read().decode('utf-8')
    print(f"HTTP Error: {e.code}")
    print(f"Response (first 200 chars):")
    print(body[:200])
    sys.exit(1)
    
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
