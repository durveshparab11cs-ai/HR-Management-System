#!/usr/bin/env python3
"""
migrate_employees.py - Create User + Employee records from EmployeeMaster data.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))

from app import create_app
from app.models.employee_master import EmployeeMaster
from app.models.employee import Employee
from app.models.user import User
from app.extensions.database import db
from werkzeug.security import generate_password_hash

app = create_app()

def migrate_employees():
    """Create User + Employee records from EmployeeMaster."""
    with app.app_context():
        masters = EmployeeMaster.query.filter(
            EmployeeMaster.user_id.is_(None)
        ).all()
        
        print("Found {} EmployeeMaster records to migrate".format(len(masters)))
        
        created = 0
        skipped = 0
        errors = 0
        
        for idx, master in enumerate(masters, start=1):
            if idx % 50 == 0:
                print("  Progress: {}/{}".format(idx, len(masters)))
            
            existing = Employee.query.filter_by(
                employee_code=master.employee_code
            ).first()
            
            if existing:
                skipped += 1
                continue
            
            try:
                user = User.query.filter_by(username=master.employee_code.lower()).first()
                
                if not user:
                    parts = master.employee_name.split()
                    first_name = parts[0] if parts else "Employee"
                    last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
                    
                    user = User(
                        username=master.employee_code.lower(),
                        email="{}@company.local".format(master.employee_code.lower()),
                        first_name=first_name,
                        last_name=last_name,
                        password_hash=generate_password_hash("temp_password_123"),
                        status='active',
                        role='employee'
                    )
                    db.session.add(user)
                    db.session.flush()
                
                emp = Employee(
                    user_id=user.id,
                    employee_code=master.employee_code,
                    department=master.department or "General",
                    designation=master.designation or "Staff",
                    date_of_birth=None,
                    gender=None,
                )
                
                db.session.add(emp)
                created += 1
                
            except Exception as e:
                errors += 1
                print("  ERROR {}: {}".format(master.employee_code, str(e)))
                db.session.rollback()
        
        try:
            db.session.commit()
            print("\nMigration complete:")
            print("   {} created".format(created))
            print("   {} skipped (already exist)".format(skipped))
            print("   {} errors".format(errors))
            
            total_employees = Employee.query.count()
            total_users = User.query.count()
            print("\nDatabase state:")
            print("   Total employees: {}".format(total_employees))
            print("   Total users: {}".format(total_users))
            
        except Exception as e:
            db.session.rollback()
            print("COMMIT FAILED: {}".format(str(e)))
            sys.exit(1)

if __name__ == "__main__":
    migrate_employees()
