#!/usr/bin/env python
"""Directly test the Flask app without going through HTTP"""

import sys
sys.path.insert(0, '.')

from app import create_app
import json

# Create the app
app = create_app('development')

# Create a test client
client = app.test_client()

# Make a POST request to the API endpoint
response = client.post(
    '/coordinator/api/search-employee',
    data=json.dumps({'employee_code': 'E-2512012'}),
    content_type='application/json'
)

print(f"Status Code: {response.status_code}")
print(f"Content-Type: {response.content_type}")
print(f"Response Text (first 200 chars):")
print(response.get_data(as_text=True)[:200])

# Try to parse as JSON
try:
    json_data = response.get_json()
    print("\n✓ Valid JSON response:")
    print(json.dumps(json_data, indent=2))
except Exception as e:
    print(f"\n✗ Invalid JSON: {e}")
    print(f"Full response:")
    print(response.get_data(as_text=True))
