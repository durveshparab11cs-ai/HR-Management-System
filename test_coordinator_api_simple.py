"""
Test the coordinator API endpoint to verify it returns JSON (200) instead of 302 redirect.
This test uses unittest.mock to avoid database connection issues.
"""

import json
import os
from unittest.mock import patch, MagicMock

# Set environment to test mode to use SQLite
os.environ['FLASK_ENV'] = 'testing'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

# Mock the database connection before creating the app
with patch('app.extensions.database.create_engine'):
    from app import create_app

app = create_app("testing")

# Mock the Employee model to avoid database lookups
with app.test_client() as client:
    with patch('app.blueprints.coordinator.routes.Employee') as mock_employee:
        # Configure the mock
        mock_employee_instance = MagicMock()
        mock_employee_instance.id = 1
        mock_employee_instance.employee_code = "E-2512012"
        mock_employee_instance.full_name = "Test Employee"
        mock_employee_instance.department = "IT"
        mock_employee_instance.designation = "Developer"
        mock_employee_instance.email = "test@example.com"
        
        # Configure the query chain
        mock_employee.query.filter_by.return_value.first.return_value = mock_employee_instance
        
        # Make the request
        response = client.post(
            "/coordinator/api/search-employee",
            data=json.dumps({"employee_code": "E-2512012"}),
            content_type="application/json"
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.content_type}")
        print()
        
        if response.status_code == 200:
            print("✅ SUCCESS: Got 200 (not 302)")
            print("✅ Response is JSON")
            print()
            print("Response Body:")
            print(json.dumps(response.get_json(), indent=2))
        elif response.status_code == 302:
            print("❌ FAIL: Still getting 302 redirect")
            print(f"Location Header: {response.headers.get('Location')}")
        else:
            print(f"⚠️  Got status code: {response.status_code}")
            print(f"Response: {response.data}")
