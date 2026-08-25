#!/usr/bin/env python
"""Test the running coordinator API server"""
import urllib.request
import json
import time
import sys

time.sleep(2)  # Wait for server to start

print("\n" + "="*70)
print("TESTING RUNNING SERVER at localhost:8000")
print("="*70 + "\n")

try:
    # Test 1: Portal loads
    print("[TEST 1] GET http://localhost:8000/coordinator/portal")
    try:
        resp = urllib.request.urlopen('http://localhost:8000/coordinator/portal', timeout=5)
        print(f"Status: {resp.status}")
        ct = resp.headers.get('Content-Type', '')
        print(f"Content-Type: {ct}")
        if resp.status == 200 and 'text/html' in ct:
            print("✓ PASS: Portal loads as HTML\n")
        else:
            print("✗ FAIL\n")
    except Exception as e:
        print(f"✗ FAIL: {e}\n")

    # Test 2: API returns JSON
    print("[TEST 2] POST http://localhost:8000/coordinator/api/search-employee")
    try:
        url = 'http://localhost:8000/coordinator/api/search-employee'
        data = json.dumps({'employee_code': 'E-2606026'}).encode('utf-8')
        req = urllib.request.Request(url, data=data, method='POST')
        req.add_header('Content-Type', 'application/json')
        
        resp = urllib.request.urlopen(req, timeout=5)
        ct = resp.headers.get('Content-Type', '')
        body = resp.read().decode('utf-8')
        
        print(f"Status: {resp.status}")
        print(f"Content-Type: {ct}")
        
        if 'application/json' in ct:
            print(f"✓ PASS: Returns JSON\n")
            try:
                data = json.loads(body)
                print(f"  Response keys: {list(data.keys())}\n")
            except:
                print(f"  Response: {body[:100]}\n")
        else:
            print(f"✗ FAIL: Not JSON")
            print(f"  Response: {body[:100]}\n")
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        print(f"Status: {e.code}")
        print(f"Error: {body[:200]}\n")
    except Exception as e:
        print(f"✗ FAIL: {e}\n")

    # Test 3: GPS endpoint
    print("[TEST 3] POST http://localhost:8000/coordinator/api/get-gps")
    try:
        url = 'http://localhost:8000/coordinator/api/get-gps'
        req = urllib.request.Request(url, data=b'{}', method='POST')
        req.add_header('Content-Type', 'application/json')
        
        resp = urllib.request.urlopen(req, timeout=5)
        body = resp.read().decode('utf-8')
        data = json.loads(body)
        
        if data.get('success'):
            print(f"Status: {resp.status}")
            print(f"GPS: {data.get('latitude')}, {data.get('longitude')}")
            print("✓ PASS\n")
        else:
            print("✗ FAIL\n")
    except Exception as e:
        print(f"✗ FAIL: {e}\n")

except KeyboardInterrupt:
    print("Interrupted")
    sys.exit(1)

print("="*70)
print("TEST COMPLETE")
print("="*70 + "\n")
