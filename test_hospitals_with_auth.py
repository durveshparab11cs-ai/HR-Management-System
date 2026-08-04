#!/usr/bin/env python
"""Test hospitals page with proper authentication."""

from app import create_app
from app.extensions.database import db
from app.models.user import User
from flask_login import FlaskLoginManager
import base64

app = create_app()

# Create a test user session
with app.test_client() as client:
    print("=" * 80)
    print("HOSPITALS PAGE TEST WITH AUTHENTICATION")
    print("=" * 80)
    
    # Get the login page
    response = client.get('/authentication/login')
    print(f"\n1. Login page status: {response.status_code}")
    
    # Try to login as admin user
    # First, let's find the admin user in database
    with app.app_context():
        admin_user = User.query.filter_by(username='e2512012').first()
        if admin_user:
            print(f"2. Found admin user: {admin_user.username} (ID: {admin_user.id})")
            
            # Try to access hospitals directly (will redirect to login)
            response = client.get('/admin/hospitals')
            print(f"3. Hospitals page status (no auth): {response.status_code}")
            
            # Try to login
            # Note: We need to use the login form
            response = client.post('/authentication/login', data={
                'username': 'e2512012',
                'password': 'Test@2512012',  # Default password from employee_master
                'remember_me': False
            }, follow_redirects=True)
            print(f"4. Login attempt status: {response.status_code}")
            print(f"   Response length: {len(response.get_data())}")
            
            # Now try to access hospitals
            response = client.get('/admin/hospitals')
            print(f"5. Hospitals page status (after login): {response.status_code}")
            
            if response.status_code == 200:
                data = response.get_data(as_text=True)
                if 'hospital' in data.lower() or 'AIIMS' in data:
                    print(f"   ✅ Hospitals page loaded successfully!")
                    print(f"   Response contains hospital data")
                else:
                    print(f"   ⚠️  Page loaded but no hospital data found")
            elif response.status_code == 500:
                data = response.get_data(as_text=True)
                print(f"   ✗ 500 Error!")
                if 'error' in data.lower():
                    print(f"   Error in response: {data[:300]}")
        else:
            print("2. Admin user not found")

print("\nDone.")
