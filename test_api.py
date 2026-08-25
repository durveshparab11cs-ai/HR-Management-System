#!/usr/bin/env python
import urllib.request
import json
import sys

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
    print(f"Status: {response.status}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Body (first 300 chars): {body[:300]}")
    print(f"Is JSON: {body.strip().startswith('{') or body.strip().startswith('[')}")
except urllib.error.HTTPError as he:
    print(f"Error {he.code}")
    print(f"Content-Type: {he.headers.get('Content-Type')}")
    body = he.read().decode('utf-8')
    print(f"Body (first 300 chars): {body[:300]}")
    print(f"Is HTML: {'<!DOCTYPE' in body or '<html' in body.lower()}")
except Exception as e:
    print(f"Exception: {type(e).__name__}: {e}")
