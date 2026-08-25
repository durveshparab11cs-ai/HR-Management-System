#!/usr/bin/env python
import urllib.request
import json

# Test coordinator API
url = "http://localhost:8000/coordinator/api/search-employee"
payload = json.dumps({"employee_code": "E-2606026"}).encode('utf-8')

req = urllib.request.Request(
    url,
    data=payload,
    headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
    method='POST'
)

try:
    response = urllib.request.urlopen(req)
    body = response.read().decode('utf-8')
    with open('test_output.txt', 'w') as f:
        f.write(f"Status: {response.status}\n")
        f.write(f"Content-Type: {response.headers.get('Content-Type')}\n")
        f.write(f"Body (first 300 chars): {body[:300]}\n")
        f.write(f"Is JSON: {body.strip().startswith(('{', '['))}\n")
except urllib.error.HTTPError as he:
    with open('test_output.txt', 'w') as f:
        f.write(f"Error {he.code}\n")
        f.write(f"Content-Type: {he.headers.get('Content-Type')}\n")
        body = he.read().decode('utf-8')
        f.write(f"Body (first 300 chars): {body[:300]}\n")
        f.write(f"Is HTML: {'<!DOCTYPE' in body or '<html' in body.lower()}\n")
except Exception as e:
    with open('test_output.txt', 'w') as f:
        f.write(f"Exception: {type(e).__name__}: {e}\n")
