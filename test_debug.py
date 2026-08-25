#!/usr/bin/env python
import time
import json
import urllib.request
import urllib.error

# Wait for server
time.sleep(2)

print("=" * 70)
print("DEBUGGING: Checking if coordinator routes are registered")
print("=" * 70)

# Test 1: Check if API endpoint exists
url = "http://localhost:8000/coordinator/api/search-employee"
payload = json.dumps({"employee_code": "E-2606026"}).encode()
req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')

print(f"\nAttempting POST to: {url}")

try:
    response = urllib.request.urlopen(req)
    body = response.read().decode('utf-8')
    
    print(f"\nStatus: {response.status}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"\nResponse body (first 500 chars):")
    print(body[:500])
    print()
    
    # Try to parse JSON
    try:
        data = json.loads(body)
        print("✓ Response IS valid JSON")
        print(json.dumps(data, indent=2)[:200])
    except json.JSONDecodeError as e:
        print(f"✗ Response is NOT valid JSON: {e}")
        if body.startswith('<'):
            print("\n⚠️  Response is HTML!")
            print("HTML snippet:")
            print(body[:300])
        
except urllib.error.HTTPError as e:
    print(f"\nHTTP Error {e.code}")
    body = e.read().decode('utf-8')
    print(f"Error body (first 300 chars):")
    print(body[:300])
    
except Exception as e:
    print(f"\n✗ ERROR: {type(e).__name__}: {e}")

print("\n" + "=" * 70)
