#!/usr/bin/env python3
"""Check if Comp Off request exists for Durvesh"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models.leave import LeaveRequest, LeaveType
from app.models.employee import Employee

app = create_app("production")

with app.app_context():
    print("="*60)
    print("CHECKING COMP OFF REQUEST")
    print("="*60)
    
    # Find Durvesh
    durvesh = Employee.query.filter_by(full_name="Durvesh Parab").first()
    if not durvesh:
        print("❌ Durvesh Parab not found")
        sys.exit(1)
    
    print(f"✅ Found Durvesh: ID={durvesh.id}, Code={durvesh.employee_code}\n")
    
    # Find CO leave type
    co_type = LeaveType.query.filter_by(code='CO').first()
    if not co_type:
        print("❌ CO leave type not found")
        sys.exit(1)
    
    print(f"✅ Found CO leave type: ID={co_type.id}, Name={co_type.name}\n")
    
    # Get all requests for Durvesh
    all_requests = LeaveRequest.query.filter_by(employee_id=durvesh.id).all()
    print(f"📊 Total leave requests for Durvesh: {len(all_requests)}")
    for lr in all_requests:
        print(f"  - {lr.leave_type.code}: {lr.start_date} to {lr.end_date} (Status: {lr.status})")
    
    print()
    
    # Get CO requests specifically
    co_requests = LeaveRequest.query.filter_by(
        employee_id=durvesh.id,
        leave_type_id=co_type.id
    ).all()
    
    print(f"🎯 CO Requests for Durvesh: {len(co_requests)}")
    if co_requests:
        for lr in co_requests:
            print(f"\n  Request ID: {lr.id}")
            print(f"  Status: {lr.status}")
            print(f"  From: {lr.start_date} To: {lr.end_date}")
            print(f"  Days: {lr.total_days}")
            print(f"  Created: {lr.applied_on}")
            print(f"  Manager Code: {lr.reporting_manager_code}")
            print(f"  Manager Name: {lr.reporting_manager_name}")
            print(f"  Comp Off Work Date: {lr.comp_off_work_date}")
            print(f"  Comp Off Expiry: {lr.comp_off_expiry_date}")
            print(f"  Comp Off Used On: {lr.comp_off_used_on}")
    else:
        print("  ❌ NO CO REQUESTS FOUND")
    
    print("\n" + "="*60)
