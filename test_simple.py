#!/usr/bin/env python
"""Minimal test to trigger coordinator API and check logs"""

from app import create_app
import json

app = create_app("development")

with app.test_client() as client:
    print("\n🔵 TEST: Calling POST /coordinator/api/search-employee")
    
    response = client.post(
        "/coordinator/api/search-employee",
        data=json.dumps({"employee_code": "E-2512012"}),
        content_type="application/json"
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response (first 200 chars): {response.data[:200]}")
