#!/usr/bin/env python3
"""Debug coordinator API - capture full response"""
import json
import sys

from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE_URL = "http://localhost:8000"
ENDPOINT = "/coordinator/api/search-employee"

payload = {"employee_code": "E-2512012"}
payload_json = json.dumps(payload).encode('utf-8')

print("=" * 70)
print("DEBUGGING COORDINATOR API")
print("=" * 70)
print(f"\nRequest: POST {BASE_URL}{ENDPOINT}")
print(f"Body: {payload}\n")

try:
    req = Request(
        f"{BASE_URL}{ENDPOINT}",
        data=payload_json,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    with urlopen(req) as response:
        status = response.status
        headers = dict(response.headers)
        body = response.read().decode('utf-8')
        
        print(f"Status: {status}")
        print(f"Headers: {json.dumps(headers, indent=2)}")
        print(f"\nBody (full):")
        print(body)
        
except HTTPError as e:
    status = e.code
    headers = dict(e.headers)
    body = e.read().decode('utf-8')
    
    print(f"HTTP Error Status: {status}")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print(f"\nBody (full):")
    print(body[:500])
    
except URLError as e:
    print(f"URL Error: {e}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
