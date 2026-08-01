#!/usr/bin/env python
"""
FINAL VERIFICATION: Admin Panel shows when logged in as e2606026
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'smart_hrms'))

from app import create_app

app = create_app()

with app.test_client() as client:
    with app.app_context():
        # Set session to logged-in as e2606026 (user ID=6)
        with client.session_transaction() as sess:
            sess['_user_id'] = "6"
        
        # Request dashboard 
        response = client.get('/dashboard/', follow_redirects=True)
        
        print("\n" + "=" * 70)
        print("ADMIN PANEL VISIBILITY TEST")
        print("=" * 70)
        print(f"Response Status: {response.status_code}")
        print(f"Admin Panel Found: {b'Admin Panel' in response.data}")
        
        if b'Admin Panel' in response.data:
            print("\n[SUCCESS] Admin Panel IS VISIBLE in sidebar!")
        else:
            print("\n[FAILED] Admin Panel NOT found in sidebar")
        
        print("=" * 70 + "\n")
