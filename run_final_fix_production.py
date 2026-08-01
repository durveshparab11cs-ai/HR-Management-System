#!/usr/bin/env python
"""
This script should be run after deploying to Render.
It fixes the e2606026 user in the production PostgreSQL database.

To run on Render:
1. SSH into the Render container 
2. Run: python run_final_fix_production.py

Or set as a render.yaml pre-deploy hook.
"""
import os
import sys

# Use production config
os.environ['FLASK_ENV'] = 'production'

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'smart_hrms'))

from app import create_app
from app.extensions.database import db
from app.models.user import User
from app.models.employee import Employee
from app.constants.enums import UserRole

def main():
    app = create_app('production')
    
    with app.app_context():
        print("=" * 70)
        print("PRODUCTION FIX: E2606026 (DURVESH PARAB)")
        print("=" * 70)
        
        user = User.query.filter_by(username='e2606026').first()
        if not user:
            print("\n[INFO] User e2606026 not found in production. This is OK.")
            print("       It will be created on first registration.")
            return
        
        print(f"\nUser Found: {user.full_name} (ID: {user.id})")
        
        # Fix 1: Password
        print("\n[1/2] Checking password...")
        if not user.check_password('TempPassword@123'):
            print("  Resetting password to TempPassword@123...")
            user.set_password('TempPassword@123')
        else:
            print("  Password is correct")
        
        # Fix 2: Employee Record
        print("\n[2/2] Checking Employee record...")
        emp = Employee.query.filter_by(user_id=user.id, is_deleted=False).first()
        if not emp:
            print("  Creating Employee record...")
            emp = Employee(
                user_id=user.id,
                employee_code='E-2606026',
                created_by=user.id,
            )
            db.session.add(emp)
        else:
            print(f"  Employee record exists: {emp.employee_code}")
        
        db.session.commit()
        print("\n[OK] All fixes applied!")
        print("=" * 70 + "\n")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
