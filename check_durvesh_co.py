#!/usr/bin/env python3
"""Check Durvesh's CO request"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models.leave import LeaveRequest, LeaveType
from app.models.employee import Employee

app = create_app("production")

with app.app_context():
    print("="*80)
    print("CHECKING DURVESH'S COMP OFF REQUEST")
    print("="*80)
    
    # Durvesh is ID=3
    durvesh = Employee.query.get(3)
    print(f"✅ Durvesh: ID={durvesh.id}, Code={durvesh.employee_code}, Name={durvesh.full_name}\n")
    
    # Find CO leave type
    co_type = LeaveType.query.filter_by(code='CO').first()
    if co_type:
        print(f"✅ CO leave type: ID={co_type.id}, Name={co_type.name}\n")
    else:
        print("❌ CO leave type not found\n")
    
    # Get all his requests
    all_requests = LeaveRequest.query.filter_by(employee_id=3).all()
    print(f"📊 All leave requests for Durvesh ({len(all_requests)}):")
    for lr in all_requests:
        print(f"  - {lr.leave_type.code}: {lr.start_date}-{lr.end_date} ({lr.status})")
    
    print()
    
    # Get CO requests
    if co_type:
        co_requests = LeaveRequest.query.filter_by(
            employee_id=3,
            leave_type_id=co_type.id
        ).all()
        
        print(f"🎯 CO Requests: {len(co_requests)}")
        if co_requests:
            for lr in co_requests:
                print(f"\n  ✅ Request ID: {lr.id}")
                print(f"     Status: {lr.status}")
                print(f"     Period: {lr.start_date} to {lr.end_date}")
                print(f"     Manager: {lr.reporting_manager_code} ({lr.reporting_manager_name})")
        else:
            print("  ❌ NO CO REQUESTS FOUND")
    
    print("\n" + "="*80)
