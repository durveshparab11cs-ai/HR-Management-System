#!/usr/bin/env python
"""
Direct test using Flask test client - no HTTP needed.
This bypasses network/PowerShell issues entirely.
"""

from app import create_app
from flask.testing import FlaskClient
import json

def test_coordinator_api():
    """Test coordinator API using Flask test client"""
    app = create_app("development")
    
    with app.test_client() as client:
        print("\n" + "=" * 70)
        print("TEST 1: Diagnostic endpoint")
        print("=" * 70)
        
        response = client.get("/coordinator/test/diagnose")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.get_json()}")
        
        print("\n" + "=" * 70)
        print("TEST 2: Search employee API")
        print("=" * 70)
        
        payload = {"employee_code": "E-2512012"}
        response = client.post(
            "/coordinator/api/search-employee",
            data=json.dumps(payload),
            content_type="application/json"
        )
        
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.content_type}")
        print(f"Response (first 300 chars): {response.data[:300].decode('utf-8')}")
        
        # Try to parse as JSON
        try:
            data = response.get_json()
            print(f"\n✓ SUCCESS: Response is valid JSON")
            print(json.dumps(data, indent=2))
        except Exception as e:
            print(f"\n✗ FAIL: Response is NOT valid JSON")
            print(f"Error: {e}")
            print(f"Full response: {response.data.decode('utf-8')}")

if __name__ == "__main__":
    test_coordinator_api()
