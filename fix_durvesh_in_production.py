#!/usr/bin/env python
"""
FIX: Create e2606026 (Durvesh Parab) with super_admin role in PRODUCTION database
This fixes the issue where e2606026 exists in dev/app/ but NOT in smart_hrms/
"""
import sys
import os

# Add smart_hrms to path so we use the production app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'smart_hrms'))

from app import create_app
from app.extensions.database import db
from app.models.user import User
from app.models.employee import Employee
from app.models.employee_master import EmployeeMaster
from app.constants.enums import UserRole, UserStatus
from datetime import datetime

app = create_app()

with app.app_context():
    print("=" * 70)
    print("CREATING E2606026 (DURVESH PARAB) AS SUPER_ADMIN IN PRODUCTION DB")
    print("=" * 70)
    
    # Check if master exists
    master = EmployeeMaster.query.filter_by(employee_code='E-2606026').first()
    if not master:
        print("ERROR: E-2606026 not found in EmployeeMaster")
        exit(1)
    
    print(f"\nMaster record found: {master.employee_name}")
    
    # Check if user already exists
    existing_user = User.query.filter_by(username='e2606026').first()
    if existing_user:
        print(f"User e2606026 already exists (ID: {existing_user.id})")
        print(f"Current role: {existing_user.role}")
        if existing_user.role != UserRole.SUPER_ADMIN.value:
            print("Updating role to super_admin...")
            existing_user.role = UserRole.SUPER_ADMIN.value
            existing_user.status = UserStatus.ACTIVE.value
            db.session.commit()
            print("Role updated successfully!")
        else:
            print("Already has super_admin role!")
        exit(0)
    
    # Create new user
    name_parts = master.employee_name.strip().split(" ", 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else "."
    
    email = f"e2606026@hrms.internal"
    username = "e2606026"
    
    # Check uniqueness
    if User.query.filter_by(email=email).first():
        email = f"e2606026_{datetime.utcnow().strftime('%s')}@hrms.internal"
    if User.query.filter_by(username=username).first():
        username = f"e2606026_{datetime.utcnow().strftime('%f')}"
    
    # Create user
    user = User(
        email=email,
        username=username,
        first_name=first_name,
        last_name=last_name,
        role=UserRole.SUPER_ADMIN.value,
        status=UserStatus.ACTIVE.value,
        email_verified=True,
    )
    user.set_password("TempPassword@123")
    db.session.add(user)
    db.session.flush()
    
    # Create employee profile
    employee = Employee(
        user_id=user.id,
        employee_code='E-2606026',
        department=master.department or None,
        designation=master.designation or None,
        created_by=user.id,
    )
    db.session.add(employee)
    
    # Mark master as registered
    master.is_registered = True
    
    db.session.commit()
    
    print(f"\n✓ User created successfully!")
    print(f"  Username: {user.username}")
    print(f"  Email: {user.email}")
    print(f"  Role: {user.role}")
    print(f"  User ID: {user.id}")
    print(f"  Employee Code: E-2606026")
    print(f"  Full Name: {user.full_name}")
    print(f"  Password: TempPassword@123")
    print("\n" + "=" * 70)
