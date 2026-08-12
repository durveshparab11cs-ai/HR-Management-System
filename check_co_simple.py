#!/usr/bin/env python3
"""Check Durvesh's CO request - simple"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models.leave import LeaveRequest, LeaveType

app = create_app("production")

with app.app_context():
    print("="*60)
    print("CHECKING DURVESH'S LEAVE REQUESTS")
    print("="*60)
    
    # Get all requests for Durvesh (ID=3)
    all_requests = LeaveRequest.query.filter_by(employee_id=3).all()
    print("Total requests for Durvesh: %d" % len(all_requests))
    
    for lr in all_requests:
        print("  - %s: %s (Status: %s)" % (lr.leave_type.code, lr.start_date, lr.status))
    
    print()
    print("="*60)
    
    # Check CO specifically
    co_type = LeaveType.query.filter_by(code='CO').first()
    if co_type:
        print("CO leave type found: ID=%d" % co_type.id)
        
        co_reqs = LeaveRequest.query.filter_by(employee_id=3, leave_type_id=co_type.id).all()
        print("CO requests: %d" % len(co_reqs))
        
        if len(co_reqs) > 0:
            for lr in co_reqs:
                print("  Found: ID=%d, Status=%s, From=%s, Manager=%s" % (lr.id, lr.status, lr.start_date, lr.reporting_manager_code))
    else:
        print("CO leave type NOT found")
    
    print("="*60)
