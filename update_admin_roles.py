#!/usr/bin/env python
"""
Update script to set super_admin role for E-2512012 and E-2603025
Run this on Render via: python update_admin_roles.py

This script is run from /app directory in the Docker container.
It imports from the 'run' module which creates the Flask app.
"""

import os
import sys

# Ensure we're in the right directory and can import the app
os.chdir('/app')
sys.path.insert(0, '/app')

try:
    from run import app
    from app.extensions.database import db
    from app.models.user import User
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("   Working directory:", os.getcwd())
    print("   Python path:", sys.path[:3])
    sys.exit(1)

def update_admin_roles():
    """Set super_admin role for the two employee codes."""
    try:
        with app.app_context():
            # Update E-2512012
            user1 = User.query.filter_by(username='e_2512012').first()
            if user1:
                print(f"Found user1 (E-2512012): {user1.email}, current role: {user1.role}")
                user1.role = 'super_admin'
                db.session.add(user1)
                print(f"  → Updated to: super_admin")
            else:
                print("❌ E-2512012 not found")
            
            # Update E-2603025
            user2 = User.query.filter_by(username='e_2603025').first()
            if user2:
                print(f"Found user2 (E-2603025): {user2.email}, current role: {user2.role}")
                user2.role = 'super_admin'
                db.session.add(user2)
                print(f"  → Updated to: super_admin")
            else:
                print("❌ E-2603025 not found")
            
            try:
                db.session.commit()
                print("\n✅ Database committed successfully!")
                print("\nVerifying changes:")
                
                # Verify
                user1_check = User.query.filter_by(username='e_2512012').first()
                user2_check = User.query.filter_by(username='e_2603025').first()
                
                if user1_check:
                    print(f"✅ E-2512012: role = '{user1_check.role}'")
                if user2_check:
                    print(f"✅ E-2603025: role = '{user2_check.role}'")
                    
            except Exception as e:
                print(f"\n❌ Error committing: {e}")
                db.session.rollback()
                sys.exit(1)
    
    except Exception as e:
        print(f"❌ Outer error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    print("=" * 60)
    print("SETTING SUPER_ADMIN ROLES FOR TWO EMPLOYEES")
    print("=" * 60)
    print()
    update_admin_roles()
    print()
    print("=" * 60)
    print("DONE!")
    print("=" * 60)
