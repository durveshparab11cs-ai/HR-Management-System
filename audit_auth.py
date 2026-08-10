#!/usr/bin/env python
"""Audit authentication system and ensure all employees can login."""

from app import create_app
from app.models.employee_master import EmployeeMaster
from app.models.user import User
from app.models.employee import Employee

app = create_app()
with app.app_context():
    print('='*60)
    print('AUTHENTICATION SYSTEM HEALTH CHECK')
    print('='*60)
    
    # 1. Check EmployeeMaster
    total_master = EmployeeMaster.query.count()
    registered_master = EmployeeMaster.query.filter_by(is_registered=True).count()
    unregistered_master = total_master - registered_master
    
    print('\n1. EMPLOYEE MASTER DATABASE:')
    print(f'   Total employees: {total_master}')
    print(f'   Registered: {registered_master}')
    print(f'   Unregistered: {unregistered_master}')
    
    # 2. Check User accounts
    total_users = User.query.filter_by(is_deleted=False).count()
    print(f'\n2. USER ACCOUNTS:')
    print(f'   Total active users: {total_users}')
    
    # 3. Check Employee profiles
    total_employees = Employee.query.filter_by(is_deleted=False).count()
    print(f'\n3. EMPLOYEE PROFILES:')
    print(f'   Total employee profiles: {total_employees}')
    
    # 4. Check for orphan records (master without user)
    orphan_master = []
    for master in EmployeeMaster.query.all():
        user = User.query.filter(User.username == master.employee_code.lower().replace('-', '')).first()
        if not user:
            orphan_master.append(master.employee_code)
    
    print(f'\n4. DATA INTEGRITY:')
    print(f'   Master codes without User accounts: {len(orphan_master)} / {total_master}')
    
    if len(orphan_master) > 0:
        print(f'\n   ISSUE FOUND: {len(orphan_master)} employees need user accounts for login!')
        print(f'   Sample codes (first 10):')
        for code in orphan_master[:10]:
            print(f'     - {code}')
        if len(orphan_master) > 10:
            print(f'     ... and {len(orphan_master) - 10} more')
        
        print('\n   SOLUTION: Auto-creating user accounts for all orphaned employees...')
        
        # Auto-create users for orphaned master records
        created_count = 0
        errors = []
        
        for code in orphan_master:
            try:
                master = EmployeeMaster.query.filter_by(employee_code=code).first()
                if not master:
                    continue
                
                # Create user
                name_parts = master.employee_name.strip().split(" ", 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else "."
                
                email = f"{code.lower().replace('-', '')}@hrms.internal"
                username = code.lower().replace("-", "")
                
                # Check for collisions
                if User.query.filter_by(email=email).first():
                    email = f"{email}.{__import__('time').time()}"
                if User.query.filter_by(username=username).first():
                    username = f"{username}_{__import__('time').time()}"
                
                # Create user with temp password
                user = User(
                    email=email,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    role='employee',
                    status='active',
                    email_verified=True,
                )
                user.set_password('TempPassword123!')
                from app.extensions.database import db
                db.session.add(user)
                db.session.flush()
                
                # Create employee profile
                employee = Employee(
                    user_id=user.id,
                    employee_code=code,
                    department=master.department or None,
                    designation=master.designation or None,
                    office_settings_id=None,
                    created_by=user.id,
                )
                db.session.add(employee)
                db.session.flush()
                
                # Mark master as registered
                master.is_registered = True
                master.user_id = user.id
                db.session.add(master)
                
                db.session.commit()
                created_count += 1
                print(f'   ✓ Created user for {code}')
                
            except Exception as e:
                db.session.rollback()
                errors.append((code, str(e)))
                print(f'   ✗ Error creating user for {code}: {e}')
        
        print(f'\n   Created: {created_count}/{len(orphan_master)} users')
        if errors:
            print(f'   Errors: {len(errors)}')
    else:
        print('\n   ✅ All employees have user accounts!')
    
    print('\n' + '='*60)
    print('FINAL STATUS:')
    print('='*60)
    
    # Re-check
    orphan_count = len([m for m in EmployeeMaster.query.all() if not User.query.filter(User.username == m.employee_code.lower().replace('-', '')).first()])
    
    if orphan_count == 0:
        print(f'✅ SUCCESS: All {total_master} employees can now login!')
    else:
        print(f'⚠️  REMAINING: {orphan_count} employees still need setup')
    
    print('='*60)
