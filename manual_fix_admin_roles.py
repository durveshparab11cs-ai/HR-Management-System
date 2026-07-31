"""
Manual script to fix super_admin roles for E-2512012 and E-2603025.

This script can be run:
1. Locally for testing: python smart_hrms/manual_fix_admin_roles.py
2. On Render via one-off dyno: 
   - Go to Resources tab
   - Click "New One-Off Dyno"
   - Run: python smart_hrms/manual_fix_admin_roles.py
3. Or via Flask shell: flask shell, then exec(open('smart_hrms/manual_fix_admin_roles.py').read())

This is a FALLBACK if the automatic startup routine fails for any reason.
"""

import sys
import os

# Ensure we're using the right paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def fix_admin_roles():
    """Manually fix super_admin roles using SQLAlchemy ORM."""
    from smart_hrms.app import create_app
    from smart_hrms.app.models.user import User
    from smart_hrms.app.models.employee import Employee
    from smart_hrms.app.models.employee_master import EmployeeMaster
    from smart_hrms.app.extensions.database import db
    
    # Create app context
    app = create_app('production')
    
    with app.app_context():
        print("=" * 70)
        print("MANUAL FIX: Super Admin Roles for E-2512012 and E-2603025")
        print("=" * 70)
        print()
        
        target_codes = [
            {'code': 'E-2512012', 'fallback_name': 'Pratik Prakash Sagvekar'},
            {'code': 'E-2603025', 'fallback_name': 'Raj Sanjay Shukla'},
        ]
        
        changes_made = False
        
        for target in target_codes:
            emp_code = target['code']
            fallback_name = target['fallback_name']
            
            print(f"Processing {emp_code}...")
            
            # Find user by employee_code through Employee table
            user = (
                db.session.query(User)
                .join(Employee, Employee.user_id == User.id)
                .filter(
                    Employee.employee_code == emp_code,
                    Employee.is_deleted == False,
                    User.is_deleted == False,
                )
                .first()
            )
            
            if user is None:
                print(f"  ⚠️  User with code {emp_code} NOT FOUND in User/Employee tables")
                print(f"  Attempting to create...")
                
                # Try to get employee info from EmployeeMaster
                emp_master = EmployeeMaster.query.filter_by(employee_code=emp_code).first()
                
                if emp_master and emp_master.employee_name:
                    print(f"  ✓ Found in EmployeeMaster: {emp_master.employee_name}")
                    full_name = emp_master.employee_name
                else:
                    print(f"  ℹ No EmployeeMaster entry, using fallback: {fallback_name}")
                    full_name = fallback_name
                
                # Split name
                name_parts = full_name.split(' ', 1)
                first_name = name_parts[0].strip() if len(name_parts) > 0 else 'Employee'
                last_name = name_parts[1].strip() if len(name_parts) > 1 else 'Account'
                
                # Create username and email
                username = emp_code.lower().replace('-', '')
                email = f"{username}@hrms.internal"
                
                print(f"  Creating: {username} / {email}")
                
                new_user = User(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    role='super_admin',
                    status='active',
                    email_verified=True,
                )
                new_user.set_password('TempPassword@123')
                
                db.session.add(new_user)
                db.session.flush()
                
                # Create Employee record
                emp_record = Employee(
                    user_id=new_user.id,
                    employee_code=emp_code,
                    created_by=new_user.id,
                )
                db.session.add(emp_record)
                
                print(f"  ✅ Staged for creation: {username} (role=super_admin)")
                changes_made = True
            
            else:
                # User exists - check/update role
                print(f"  ✓ Found user: {user.username} (ID={user.id})")
                print(f"  Current role: {user.role}")
                
                if user.role != 'super_admin':
                    print(f"  ⚠️  Updating role from '{user.role}' to 'super_admin'...")
                    user.role = 'super_admin'
                    db.session.add(user)
                    print(f"  ✅ Role updated to super_admin")
                    changes_made = True
                else:
                    print(f"  ✓ Already has role=super_admin (no change needed)")
            
            print()
        
        # Commit changes
        if changes_made:
            try:
                db.session.commit()
                print("✅ ALL CHANGES COMMITTED SUCCESSFULLY")
                print()
            except Exception as e:
                print(f"❌ COMMIT FAILED: {e}")
                db.session.rollback()
                print("Changes rolled back.")
                return False
        else:
            print("✓ No changes needed - both users already have super_admin role")
            print()
        
        # Final verification
        print("FINAL VERIFICATION:")
        print("-" * 70)
        
        for target in target_codes:
            emp_code = target['code']
            
            final_user = (
                db.session.query(User)
                .join(Employee, Employee.user_id == User.id)
                .filter(
                    Employee.employee_code == emp_code,
                    Employee.is_deleted == False,
                    User.is_deleted == False,
                )
                .first()
            )
            
            if final_user:
                status = "✅" if final_user.role == 'super_admin' else "❌"
                print(f"{status} {emp_code}")
                print(f"   Username: {final_user.username}")
                print(f"   Email: {final_user.email}")
                print(f"   Role: {final_user.role}")
                print(f"   Status: {final_user.status}")
            else:
                print(f"❌ {emp_code} - NOT FOUND after commit")
            print()
        
        print("=" * 70)
        print("FIX COMPLETE")
        print("=" * 70)
        return True


if __name__ == '__main__':
    try:
        success = fix_admin_roles()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
