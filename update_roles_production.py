#!/usr/bin/env python
"""
Direct SQL update script for production database.
Updates E-2512012 and E-2603025 roles to super_admin in the Render PostgreSQL database.

This is a one-time fix for the production website.
Run via: python update_roles_production.py
"""

import os
import sys

# Add the smart_hrms directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Update roles directly in production database."""
    from run import app
    from app.extensions.database import db
    from sqlalchemy import text
    
    print("=" * 70)
    print("PRODUCTION DATABASE ROLE UPDATE")
    print("=" * 70)
    print()
    
    with app.app_context():
        try:
            print("1. Checking current state of users table...")
            result = db.session.execute(text("""
                SELECT id, username, email, role 
                FROM users 
                WHERE username IN ('e_2512012', 'e_2603025')
            """))
            
            current_users = result.fetchall()
            print(f"\n   Found {len(current_users)} matching users:")
            for row in current_users:
                print(f"   - ID: {row[0]}, Username: {row[1]}, Email: {row[2]}, Role: {row[3]}")
            
            if len(current_users) == 0:
                print("\n   ⚠️  No users found with these usernames!")
                print("   The users may not exist in the database yet.")
                print("   The app startup function should create them on next deployment.")
                print()
            else:
                print("\n2. Updating roles to 'super_admin'...")
                update_result = db.session.execute(text("""
                    UPDATE users 
                    SET role = 'super_admin'
                    WHERE username IN ('e_2512012', 'e_2603025')
                """))
                db.session.commit()
                
                print(f"   ✅ Updated {update_result.rowcount} user(s)")
                print()
                
                print("3. Verifying changes...")
                verify_result = db.session.execute(text("""
                    SELECT id, username, email, role 
                    FROM users 
                    WHERE username IN ('e_2512012', 'e_2603025')
                """))
                
                verified_users = verify_result.fetchall()
                for row in verified_users:
                    status = "✅" if row[3] == 'super_admin' else "❌"
                    print(f"   {status} Username: {row[1]}, Role: {row[3]}")
                
                print()
                print("=" * 70)
                print("✅ PRODUCTION ROLES UPDATED SUCCESSFULLY")
                print("=" * 70)
                print()
                print("Both users should now see the admin dashboard.")
                print()
        
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            sys.exit(1)

if __name__ == '__main__':
    main()
