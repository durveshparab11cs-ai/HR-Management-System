#!/usr/bin/env python3
"""Test local API directly"""
import sys
sys.path.insert(0, '.')

from app import create_app
import json

app = create_app('development')
client = app.test_client()

print("=" * 60)
print("TESTING LOCAL API: /coordinator/api/search-employee")
print("=" * 60)

# Test 1: Valid employee
print("\n[TEST 1] Valid employee code E-2512012")
response = client.post(
    '/coordinator/api/search-employee',
    data=json.dumps({'employee_code': 'E-2512012'}),
    content_type='application/json'
)

print(f"Status: {response.status_code}")
print(f"Content-Type: {response.content_type}")
print(f"First 200 chars: {response.get_data(as_text=True)[:200]}")

try:
    json_data = response.get_json()
    print(f"✓ Valid JSON: {json.dumps(json_data, indent=2)[:300]}")
except Exception as e:
    print(f"✗ NOT JSON: {e}")
    print(f"Response text: {response.get_data(as_text=True)[:500]}")

# Test 2: Invalid employee
print("\n[TEST 2] Invalid employee code INVALID-9999")
response = client.post(
    '/coordinator/api/search-employee',
    data=json.dumps({'employee_code': 'INVALID-9999'}),
    content_type='application/json'
)

print(f"Status: {response.status_code}")
print(f"Content-Type: {response.content_type}")

try:
    json_data = response.get_json()
    print(f"✓ Valid JSON: {json.dumps(json_data, indent=2)}")
except Exception as e:
    print(f"✗ NOT JSON: {e}")

print("\n" + "=" * 60)
