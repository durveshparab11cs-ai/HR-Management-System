#!/usr/bin/env python
"""Debug script to check checkout time format in the database"""

import sys
import os

sys.path.insert(0, os.getcwd())
os.chdir(os.getcwd())

from app import create_app
from app.models.attendance import Attendance
from datetime import date

app = create_app('production')

with app.app_context():
    # Get any recent attendance record with checkout time
    att = Attendance.query.filter(
        Attendance.check_out_time.isnot(None)
    ).order_by(Attendance.id.desc()).limit(1).first()
    
    if att:
        print(f"Attendance ID: {att.id}")
        print(f"Check-out Time Type: {type(att.check_out_time)}")
        print(f"Check-out Time Value: {att.check_out_time}")
        print(f"Check-out Time Repr: {repr(att.check_out_time)}")
        if hasattr(att.check_out_time, 'strftime'):
            print(f"Can strftime: {att.check_out_time.strftime('%H:%M')}")
            print(f"ISO format: {att.check_out_time.isoformat()}")
        else:
            print("ERROR: check_out_time is not a datetime object!")
            print(f"It is: {type(att.check_out_time)}")
    else:
        print("No attendance records with checkout time found")
        # Try to get any record
        recent = Attendance.query.order_by(Attendance.id.desc()).limit(1).first()
        if recent:
            print(f"Recent attendance: ID={recent.id}, check_in={recent.check_in_time}, check_out={recent.check_out_time}")
