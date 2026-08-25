#!/usr/bin/env python3
"""Direct API test by calling Flask app directly"""

import sys
import os

os.chdir(r"c:\Users\Administrator\Documents\HRMS\smart_hrms")
sys.path.insert(0, os.getcwd())

from app import create_app
from app.extensions.database import db

app = create_app("development")

with app.app_context():
    # Print all registered routes
    print("\n" + "="*80)
    print("ALL REGISTERED ROUTES:")
    print("="*80)
    
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
        if 'coordinator' in rule.rule.lower():
            methods = ','.join(rule.methods - {'HEAD', 'OPTIONS'})
            print(f"{rule.rule:50} | {methods:20} | {rule.endpoint}")
    
    # Test the API endpoint directly
    print("\n" + "="*80)
    print("TESTING API ENDPOINT DIRECTLY:")
    print("="*80)
    
    with app.test_client() as client:
        print("\n1. Testing search-employee endpoint:")
        resp = client.post(
            '/coordinator/api/search-employee',
            json={"employee_code": "E-2606026"},
            content_type='application/json'
        )
        
        print(f"   Status: {resp.status_code}")
        print(f"   Content-Type: {resp.content_type}")
        print(f"   Data type: {type(resp.data)}")
        print(f"   Data (first 200 chars): {resp.data[:200]}")
        
        # Try to parse as JSON
        try:
            data = resp.get_json()
            print(f"   ✓ Valid JSON: {data}")
        except:
            print(f"   ✗ NOT valid JSON!")
            print(f"   Raw response: {resp.data.decode('utf-8')[:500]}")
    
    print("\n" + "="*80)
