#!/usr/bin/env python
"""Test to check what routes are registered"""

import sys
sys.path.insert(0, '.')

from app import create_app

app = create_app()

print("=" * 70)
print("REGISTERED ROUTES")
print("=" * 70)

# Get all routes
for rule in app.url_map.iter_rules():
    if 'coordinator' in rule.rule:
        print(f"{rule.rule:50} | Methods: {','.join(rule.methods - {'HEAD', 'OPTIONS'})}")

print("\n" + "=" * 70)
print("Coordinator API endpoints registered:")
count = 0
for rule in app.url_map.iter_rules():
    if '/coordinator/api/' in rule.rule:
        print(f"  ✓ {rule.rule}")
        count += 1

print(f"\nTotal coordinator API routes: {count}")

# Try to access the search-employee endpoint
print("\n" + "=" * 70)
print("Testing /coordinator/api/search-employee")
print("=" * 70)

with app.test_client() as client:
    response = client.post('/coordinator/api/search-employee', 
                          json={"employee_code": "E-2606026"},
                          headers={'Content-Type': 'application/json'})
    
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Response length: {len(response.get_data(as_text=True))}")
    
    text = response.get_data(as_text=True)[:100]
    print(f"Response preview: {text}")
    
    if text.startswith('{'):
        print("✓ Response is JSON")
    elif text.startswith('<'):
        print("✗ Response is HTML (bug!)")
    else:
        print("? Response is something else")
