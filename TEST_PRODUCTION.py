#!/usr/bin/env python3
"""
TEST SCRIPT: Verify Comp Off is working in production
This tests the actual /leave/ endpoint to see what's returned
"""

import os
import sys
from pathlib import Path

os.environ['FLASK_ENV'] = 'production'
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app
from app.extensions.database import db
from app.models.leave import LeaveType, LeaveRequest
from app.models.employee import Employee
from app.models.user import User

def test():
    app = create_app('production')
    
    with app.app_context():
        print("\n" + "="*80)
        print("PRODUCTION DIAGNOSTIC TEST")
        print("="*80 + "\n")
        
        # Test 1: Leave types
        print("[TEST 1] Leave Types in Database")
        all_lt = LeaveType.query.all()
        print(f"Total: {len(all_lt)}")
        for lt in all_lt:
            print(f"  {lt.code:6} | {lt.name:25} | is_active={lt.is_active}")
        
        co_type = LeaveType.query.filter(LeaveType.code.in_(['CO', 'COMP'])).first()
        if co_type:
            print(f"\n✓ Comp Off found: code='{co_type.code}' (ID={co_type.id})")
        else:
            print(f"\n❌ Comp Off NOT found!")
        print()
        
        # Test 2: Employees
        print("[TEST 2] Employees in Database")
        emps = Employee.query.limit(3).all()
        print(f"Sample employees (first 3):")
        for emp in emps:
            emp_name = f"{getattr(emp, 'first_name', '?')} {getattr(emp, 'last_name', '?')}"
            print(f"  ID={emp.id} | {emp_name} | user_id={emp.user_id}")
        print()
        
        # Test 3: Leave requests
        print("[TEST 3] Leave Requests in Database")
        lr_count = LeaveRequest.query.count()
        print(f"Total leave requests: {lr_count}")
        
        if co_type:
            co_lr = LeaveRequest.query.filter_by(leave_type_id=co_type.id).all()
            print(f"Comp Off requests (code='{co_type.code}'): {len(co_lr)}")
            for lr in co_lr[:3]:
                print(f"  ID={lr.id} | emp_id={lr.employee_id} | status={lr.status}")
        print()
        
        # Test 4: Call get_balance for first employee
        print("[TEST 4] Testing get_balance()")
        if emps:
            emp_id = emps[0].id
            emp_name = f"{getattr(emps[0], 'first_name', '?')} {getattr(emps[0], 'last_name', '?')}"
            print(f"Testing for employee ID={emp_id} ({emp_name})")
            
            from app.blueprints.leave.service import LeaveService
            svc = LeaveService()
            balances = svc.get_balance(emp_id)
            
            print(f"Balances returned: {len(balances)}")
            for b in balances:
                available_val = b.get('available', '?')
                try:
                    comp = available_val >= 0 if isinstance(available_val, (int, float)) else True
                    status = "✓"
                except:
                    status = "?"
                print(f"  {status} {b['type'].code:6} | {b['type'].name:25} | available={available_val}")
            
            # Check if CO is in balances
            co_balance = next((b for b in balances if b['type'].code in ['CO', 'COMP']), None)
            if co_balance:
                print(f"\n✓ Comp Off BALANCE FOUND!")
                print(f"  Code: {co_balance['type'].code}")
                print(f"  Max: {co_balance['max']}")
                print(f"  Available: {co_balance['available']}")
                print(f"  Taken: {co_balance['taken']}")
            else:
                print(f"\n❌ Comp Off BALANCE NOT FOUND!")
                print(f"  Balances returned: {[b['type'].code for b in balances]}")
        print()
        
        print("="*80)
        print("DIAGNOSTIC COMPLETE")
        print("="*80)

if __name__ == '__main__':
    test()
