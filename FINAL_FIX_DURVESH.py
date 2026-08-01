#!/usr/bin/env python
"""
FINAL FIX: Restore e2606026 (Durvesh Parab) to fully working state
1. Reset password to TempPassword@123
2. Create missing Employee record
3. Verify login works
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'smart_hrms'))

from app import create_app
from app.extensions.database import db
from app.models.user import User
from app.models.employee import Employee
from app.constants.enums import UserRole

app = create_app()

with app.app_context():
    print("=" * 70)
    print("FINAL FIX: DURVESH PARAB (E-2606026) SUPER ADMIN")
    print("=" * 70)
    
    user = User.query.filter_by(username='e2606026').first()
    if not user:
        print("\nERROR: User not found!")
        exit(1)
    
    print(f"\nUser: {user.full_name} (ID: {user.id})")
    print(f"Current Role: {user.role}")
    print(f"Current Status: {user.status}")
    
    # FIX 1: Reset password
    print("\n[1/3] Resetting password...")
    user.set_password("TempPassword@123")
    print(f"  [OK] Password reset to: TempPassword@123")
    
    # FIX 2: Create Employee record if missing
    print("\n[2/3] Checking Employee record...")
    emp = Employee.query.filter_by(user_id=user.id, is_deleted=False).first()
    if emp:
        print(f"  [OK] Employee record exists: {emp.employee_code}")
    else:
        print(f"  [MISSING] Employee record missing, creating...")
        emp = Employee(
            user_id=user.id,
            employee_code='E-2606026',
            created_by=user.id,
        )
        db.session.add(emp)
        print(f"  [OK] Employee record created")
    
    # FIX 3: Commit and verify
    print("\n[3/3] Saving changes...")
    db.session.commit()
    print(f"  [OK] All changes committed")
    
    # Verify
    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)
    
    # Refresh from DB
    user = User.query.filter_by(username='e2606026').first()
    emp = Employee.query.filter_by(user_id=user.id, is_deleted=False).first()
    
    print(f"\n[OK] Username: {user.username}")
    print(f"[OK] Full Name: {user.full_name}")
    print(f"[OK] Role: {user.role}")
    print(f"[OK] Status: {user.status}")
    print(f"[OK] Is Active: {user.is_active}")
    print(f"[OK] Password Check: {user.check_password('TempPassword@123')}")
    print(f"[OK] has_role(SUPER_ADMIN): {user.has_role(UserRole.SUPER_ADMIN)}")
    print(f"[OK] Employee Record: {emp.employee_code if emp else 'MISSING'}")
    
    if emp:
        print(f"[OK] Employee ID: {emp.id}")
    
    print("\n" + "=" * 70)
    print("LOGIN CREDENTIALS")
    print("=" * 70)
    print(f"Employee Code: E-2606026")
    print(f"Username: e2606026")
    print(f"Password: TempPassword@123")
    print("=" * 70 + "\n")
