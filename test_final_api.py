#!/usr/bin/env python
import urllib.request, json, time
time.sleep(3)  # Give server time to start

url = "http://localhost:8000/coordinator/api/search-employee"
payload = json.dumps({"employee_code": "E-2606026"}).encode()
req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')

print("Testing: POST /coordinator/api/search-employee")
print("Payload: {\"employee_code\": \"E-2606026\"}")
print()

try:
    response = urllib.request.urlopen(req)
    body = response.read().decode('utf-8')
    print(f"HTTP Status: {response.status}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print()
    
    data = json.loads(body)
    print("Response Body (JSON):")
    print(json.dumps(data, indent=2))
    print()
    print("✓ SUCCESS - API returned JSON (not HTML)")
    
    if data.get('success'):
        print(f"✓ Employee found: {data['employee']['full_name']}")
    else:
        print(f"ℹ Employee not in database: {data.get('error')}")
        
except urllib.error.HTTPError as e:
    body = e.read().decode('utf-8')
    print(f"HTTP Error: {e.code}")
    if body.startswith('<'):
        print("✗ FAILED - Received HTML instead of JSON")
        print(f"HTML snippet: {body[:200]}")
    else:
        data = json.loads(body)
        print(f"Response: {json.dumps(data, indent=2)}")
        
except json.JSONDecodeError as e:
    print(f"✗ FAILED - Response is not valid JSON: {e}")
    print(f"Body: {body[:300]}")
    
except Exception as e:
    print(f"✗ FAILED - {type(e).__name__}: {e}")
