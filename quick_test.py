#!/usr/bin/env python
"""Quick test of coordinator API after fix"""
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app

app = create_app("development")
client = app.test_client()

print("\n" + "="*70)
print("TESTING COORDINATOR API - QUICK TEST")
print("="*70 + "\n")

# Test 1: Portal loads
print("[TEST 1] GET /coordinator/portal")
resp = client.get('/coordinator/portal')
print(f"Status: {resp.status_code}")
print(f"Is HTML: {'text/html' in resp.content_type}")
if resp.status_code == 200:
    print("✓ PASS: Portal loads\n")
else:
    print("✗ FAIL\n")

# Test 2: API returns JSON
print("[TEST 2] POST /coordinator/api/search-employee")
resp = client.post(
    '/coordinator/api/search-employee',
    json={'employee_code': 'E-2606026'},
    content_type='application/json'
)
print(f"Status: {resp.status_code}")
print(f"Content-Type: {resp.content_type}")

try:
    data = resp.get_json()
    print(f"Is JSON: True")
    print(f"Response: {json.dumps(data, indent=2)[:200]}")
    if 'success' in data:
        print("✓ PASS: Returns JSON with success key\n")
    else:
        print("✗ FAIL: No success key\n")
except Exception as e:
    print(f"✗ FAIL: Not valid JSON - {e}\n")

# Test 3: GPS endpoint
print("[TEST 3] POST /coordinator/api/get-gps")
resp = client.post('/coordinator/api/get-gps')
print(f"Status: {resp.status_code}")
try:
    data = resp.get_json()
    if data.get('success'):
        print(f"GPS: {data.get('latitude')}, {data.get('longitude')}")
        print("✓ PASS\n")
    else:
        print("✗ FAIL\n")
except:
    print("✗ FAIL: Not JSON\n")

print("="*70)
print("QUICK TEST COMPLETE")
print("="*70 + "\n")
