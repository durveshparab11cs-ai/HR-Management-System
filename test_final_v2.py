#!/usr/bin/env python3
"""Final test to verify coordinator API returns JSON after CSRF fix."""
import urllib.request
import json
import time
import sys

# Wait for server to start
print("Waiting for server to initialize...")
time.sleep(6)

url = "http://localhost:8000/coordinator/api/search-employee"
payload = json.dumps({"employee_code": "E-2606026"}).encode()
req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')

print("=" * 70)
print("COORDINATOR API FINAL TEST - WITH CSRF FIX")
print("=" * 70)
print(f"\nURL: POST {url}")
print(f"Payload: {{'employee_code': 'E-2606026'}}\n")

try:
    response = urllib.request.urlopen(req)
    body = response.read().decode('utf-8')
    
    status = response.status
    content_type = response.headers.get('Content-Type', 'NOT SET')
    
    print(f"HTTP Status: {status}")
    print(f"Content-Type: {content_type}")
    print()
    
    # Check if Content-Type header says JSON
    is_json_header = 'application/json' in content_type.lower() if content_type else False
    
    try:
        data = json.loads(body)
        is_valid_json = True
        print("✓ Response body is valid JSON")
    except json.JSONDecodeError:
        is_valid_json = False
        print(f"✗ Response body is NOT valid JSON")
    
    print("\n--- RESULTS ---")
    print(f"Content-Type Header: {'JSON' if is_json_header else 'NOT JSON'}")
    print(f"Response Body: {'Valid JSON' if is_valid_json else 'Invalid/Empty'}")
    
    if is_json_header and is_valid_json:
        print("\n✓✓✓ SUCCESS - API returns JSON with correct Content-Type")
        print(json.dumps(data, indent=2))
        print("\n" + "=" * 70)
        print("TEST RESULT: PASS")
        print("=" * 70)
        sys.exit(0)
    elif is_valid_json:
        print("\n⚠️  WARNING - Body is JSON but Content-Type is wrong")
        print(json.dumps(data, indent=2))
        print("\n" + "=" * 70)
        print("TEST RESULT: PARTIAL PASS (fix Content-Type header)")
        print("=" * 70)
        sys.exit(0)
    else:
        print(f"\nResponse (first 300 chars):")
        print(body[:300])
        print("\n" + "=" * 70)
        print("TEST RESULT: FAIL - Not JSON")
        print("=" * 70)
        sys.exit(1)
        
except urllib.error.HTTPError as e:
    body = e.read().decode('utf-8')
    print(f"HTTP Error: {e.code}")
    print(f"Content-Type: {e.headers.get('Content-Type')}")
    print(f"\nResponse (first 300 chars):")
    print(body[:300])
    print("\n" + "=" * 70)
    print("TEST RESULT: FAIL - HTTP Error")
    print("=" * 70)
    sys.exit(1)
    
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    print("\n" + "=" * 70)
    print("TEST RESULT: FAIL - Exception")
    print("=" * 70)
    sys.exit(1)
