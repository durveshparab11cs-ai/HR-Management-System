#!/usr/bin/env python
"""
Debug: Check current state of e2606026 in production database
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'smart_hrms'))

from app import create_app
from app.models.user import User
from app.constants.enums import UserRole

app = create_app()

with app.app_context():
    user = User.query.filter_by(username='e2606026').first()
    
    print("\n=== USER STATE DEBUG ===\n")
    print(f"Username: {user.username}")
    print(f"Email: {user.email}")
    print(f"Full Name: {user.full_name}")
    print(f"ID: {user.id}")
    print(f"Role (raw): {user.role!r}")
    print(f"Role == 'super_admin': {user.role == 'super_admin'}")
    print(f"Role == UserRole.SUPER_ADMIN.value: {user.role == UserRole.SUPER_ADMIN.value}")
    print(f"Is Active: {user.is_active}")
    print(f"Status: {user.status}")
    print(f"Is Deleted: {user.is_deleted}")
    print(f"has_role(SUPER_ADMIN): {user.has_role(UserRole.SUPER_ADMIN)}")
    print(f"Password check TempPassword@123: {user.check_password('TempPassword@123')}")
    
    # Check employee record
    emp = user.employee
    if emp:
        print(f"\nEmployee record: YES")
        print(f"  Employee Code: {emp.employee_code}")
        print(f"  Department: {emp.department}")
    else:
        print(f"\nEmployee record: NO")
    
    print("\n=== END DEBUG ===\n")
