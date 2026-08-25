#!/usr/bin/env python
import time
import json
import urllib.request

# Wait for server
time.sleep(2)

url = "http://localhost:8000/coordinator/api/search-employee"
payload = json.dumps({"employee_code": "E-2606026"}).encode('utf-8')

req = urllib.request.Request(
    url, 
    data=payload,
    headers={'Content-Type': 'application/json'},
    method='POST'
)

# Open output file with UTF-8 encoding
with open("test_result.txt", "w", encoding="utf-8") as f:
    try:
        response = urllib.request.urlopen(req)
        body = response.read().decode('utf-8')
        
        f.write(f"Status: {response.status}\n")
        f.write(f"Content-Type: {response.headers.get('Content-Type')}\n")
        
        try:
            data = json.loads(body)
            f.write("Valid JSON: YES\n")
            f.write(json.dumps(data, indent=2))
        except json.JSONDecodeError as e:
            f.write("Valid JSON: NO\n")
            f.write(f"Error: {e}\n")
            f.write(f"Body: {body[:500]}\n")
            
    except urllib.error.HTTPError as he:
        body = he.read().decode('utf-8')
        f.write(f"HTTP Error {he.code}\n")
        f.write(f"Content-Type: {he.headers.get('Content-Type')}\n")
        f.write(f"Body: {body[:500]}\n")
    except Exception as e:
        f.write(f"Exception: {str(e)}\n")

# Also print to console
with open("test_result.txt", "r", encoding="utf-8") as f:
    print(f.read())
