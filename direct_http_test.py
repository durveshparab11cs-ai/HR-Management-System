#!/usr/bin/env python
"""Directly test what the HTTP server returns"""
import urllib.request
import json
import time
import sys

print("Waiting 3 seconds for server to start...")
time.sleep(3)

print("\n" + "="*80)
print("DIRECT HTTP TEST - What is the server ACTUALLY returning?")
print("="*80 + "\n")

# Test 1: Portal
print("[TEST 1] GET http://localhost:8000/coordinator/portal")
try:
    with urllib.request.urlopen('http://localhost:8000/coordinator/portal', timeout=3) as resp:
        status = resp.status
        ct = resp.headers.get('Content-Type', 'unknown')
        body = resp.read(100)
        print(f"Status: {status}")
        print(f"Content-Type: {ct}")
        print(f"Body starts with: {body[:50]}")
except Exception as e:
    print(f"ERROR: {e}")

# Test 2: API
print("\n[TEST 2] POST http://localhost:8000/coordinator/api/search-employee")
try:
    data = json.dumps({'employee_code': 'E-2606026'}).encode('utf-8')
    req = urllib.request.Request(
        'http://localhost:8000/coordinator/api/search-employee',
        data=data,
        method='POST',
        headers={'Content-Type': 'application/json'}
    )
    
    with urllib.request.urlopen(req, timeout=3) as resp:
        status = resp.status
        ct = resp.headers.get('Content-Type', 'unknown')
        body_raw = resp.read()
        
        print(f"Status: {status}")
        print(f"Content-Type: {ct}")
        print(f"Body (first 300 chars): {body_raw[:300]}")
        
        # Try to parse as JSON
        try:
            body_json = json.loads(body_raw)
            print(f"Parsed JSON: {json.dumps(body_json, indent=2)[:200]}")
        except:
            print(f"NOT valid JSON!")
            
except urllib.error.HTTPError as e:
    status = e.code
    ct = e.headers.get('Content-Type', 'unknown')
    body = e.read(300)
    print(f"Status: {status}")
    print(f"Content-Type: {ct}")
    print(f"Body: {body}")
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "="*80 + "\n")
