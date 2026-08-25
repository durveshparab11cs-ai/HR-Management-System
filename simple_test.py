#!/usr/bin/env python
import time
time.sleep(3)  # Wait for server

try:
    import urllib.request, json
    url = "http://localhost:8000/coordinator/api/search-employee"
    payload = json.dumps({"employee_code": "E-2606026"}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
    
    response = urllib.request.urlopen(req)
    body = response.read().decode('utf-8')
    
    print("✓ Status:", response.status)
    print("✓ Content-Type:", response.headers.get('Content-Type'))
    
    try:
        data = json.loads(body)
        print("✓ Valid JSON Response:")
        print(json.dumps(data, indent=2))
    except:
        print("✗ NOT JSON:", body[:200])
        
except Exception as e:
    print("✗ Error:", str(e))
