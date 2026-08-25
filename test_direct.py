#!/usr/bin/env python3
"""Direct test using Flask test client"""
import sys
import json

# Add app directory to path
sys.path.insert(0, '.')

from app import create_app

app = create_app("development")

with app.test_client() as client:
    response = client.post(
        '/coordinator/api/search-employee',
        json={"employee_code": "E-2512012"},
        content_type='application/json'
    )
    
    print("=" * 70)
    print("DIRECT TEST RESULT")
    print("=" * 70)
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Body:\n{response.get_data(as_text=True)}")
    print()
    
    # Check result
    if response.status_code in [301, 302, 303, 307, 308]:
        print("❌ FAILED: Got redirect (302 bug still present)")
        sys.exit(1)
    
    try:
        data = response.get_json()
        print("✅ SUCCESS: Got JSON response (not 302 HTML)")
        print(f"   Success: {data.get('success')}")
        sys.exit(0)
    except:
        print("❌ FAILED: Response is not JSON")
        sys.exit(1)
