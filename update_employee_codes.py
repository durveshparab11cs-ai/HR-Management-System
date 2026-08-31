"""
Update employee codes for specific employees.
This script updates employee codes in both employee_master and employees tables.
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions.database import db
from app.models.employee_master import EmployeeMaster
from app.models.employee import Employee

def update_employee_codes():
    """Update employee codes for Pratiksha and Nilam."""
    app = create_app()
    
    with app.app_context():
        print("Starting employee code update...")
        
        # Update 1: Pratiksha Suresh Bhalerao
        # Find by name
        pratiksha_master = EmployeeMaster.query.filter(
            EmployeeMaster.employee_name.ilike('%Pratiksha%Bhalerao%')
        ).first()
        
        if pratiksha_master:
            old_code_1 = pratiksha_master.employee_code
            pratiksha_master.employee_code = 'E-2604012'
            print(f"✓ Updated {pratiksha_master.employee_name}: {old_code_1} → E-2604012")
            
            # Also update in employees table
            pratiksha_emp = Employee.query.filter_by(employee_code=old_code_1).first()
            if pratiksha_emp:
                pratiksha_emp.employee_code = 'E-2604012'
                print(f"  ✓ Updated in employees table as well")
        else:
            print("✗ Pratiksha Suresh Bhalerao not found")
        
        # Update 2: Nilam Narayan Shigwan
        nilam_master = EmployeeMaster.query.filter(
            EmployeeMaster.employee_name.ilike('%Nilam%Shigwan%')
        ).first()
        
        if nilam_master:
            old_code_2 = nilam_master.employee_code
            nilam_master.employee_code = 'E-2604009'
            print(f"✓ Updated {nilam_master.employee_name}: {old_code_2} → E-2604009")
            
            # Also update in employees table
            nilam_emp = Employee.query.filter_by(employee_code=old_code_2).first()
            if nilam_emp:
                nilam_emp.employee_code = 'E-2604009'
                print(f"  ✓ Updated in employees table as well")
        else:
            print("✗ Nilam Narayan Shigwan not found")
        
        # Commit all changes
        try:
            db.session.commit()
            print("\n✅ All changes committed successfully!")
            print("\nThey can now login with:")
            print("  - Pratiksha: E-2604012")
            print("  - Nilam: E-2604009")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error committing changes: {e}")
            return False
        
        return True

if __name__ == '__main__':
    success = update_employee_codes()
    sys.exit(0 if success else 1)
