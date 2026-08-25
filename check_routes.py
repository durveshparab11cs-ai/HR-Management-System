#!/usr/bin/env python
"""Check what routes are registered in the Flask app"""
import sys
import os

# Ensure we're using the local smart_hrms app
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app

print("\n" + "="*80)
print("CHECKING ROUTES REGISTERED IN FLASK APP")
print("="*80 + "\n")

app = create_app("development")

print("Total routes:", len(list(app.url_map.iter_rules())))
print("\nCoordinator routes:")
for rule in app.url_map.iter_rules():
    if 'coordinator' in rule.rule:
        print(f"  {rule.rule:60} | {','.join(rule.methods)} | {rule.endpoint}")

print("\nSearching for /coordinator/api/search-employee:")
found = False
for rule in app.url_map.iter_rules():
    if '/coordinator/api/search-employee' in rule.rule:
        print(f"  ✓ FOUND: {rule.rule} | {rule.methods} | {rule.endpoint}")
        found = True

if not found:
    print("  ✗ NOT FOUND - THIS IS THE PROBLEM!")

print("\nAll /api/ routes:")
for rule in app.url_map.iter_rules():
    if '/api/' in rule.rule or '/coordinator/api' in rule.rule:
        print(f"  {rule.rule:60} | {rule.methods} | {rule.endpoint}")

print("\n" + "="*80)
print("TESTING API DIRECTLY")
print("="*80 + "\n")

client = app.test_client()

print("Test 1: POST /coordinator/api/search-employee")
resp = client.post(
    '/coordinator/api/search-employee',
    json={'employee_code': 'E-2606026'},
    content_type='application/json'
)
print(f"Status: {resp.status_code}")
print(f"Content-Type: {resp.content_type}")
print(f"Body (first 200 chars): {resp.data[:200]}")

if 'application/json' in resp.content_type:
    print("✓ RETURNS JSON")
else:
    print("✗ NOT JSON - RETURNS:", resp.content_type)

print("\n" + "="*80 + "\n")
