#!/usr/bin/env python3
"""
Test script to debug status calculation
"""
import sys
from datetime import datetime, timedelta, time
sys.path.insert(0, '/workspace')

from app import create_app
from app.blueprints.attendance.attendance_engine import compute_check_out_meta
from app.blueprints.attendance.constants import AttendanceStatus
from app.models.office_settings import OfficeSettings
from app.models.attendance import Attendance

app = create_app()

with app.app_context():
    # Get today's attendance records
    from datetime import date
    today = date.today()
    
    # Get all attendance for today
    from app.blueprints.attendance.repository import AttendanceRepository
    repo = AttendanceRepository()
    records = repo.get_all_today(today)
    
    print(f"\n{'='*80}")
    print(f"Testing {len(records)} attendance records for {today}")
    print(f"{'='*80}\n")
    
    for i, att in enumerate(records[:5]):  # Test first 5
        print(f"\n[{i+1}] Employee: {att.employee.full_name}")
        print(f"    ID: {att.id}")
        print(f"    Check-In: {att.check_in_time}")
        print(f"    Check-Out: {att.check_out_time}")
        print(f"    DB Status: {att.status}")
        print(f"    DB Working Minutes: {att.working_minutes}")
        
        # Get office
        office = repo.get_office_for_employee(att.employee)
        if office:
            print(f"    Office Start: {office.office_start_time}")
            print(f"    Office End: {office.office_end_time}")
            print(f"    Half-day threshold: {office.half_day_threshold_minutes} min")
            
            # Try to compute
            try:
                calc_time = att.check_out_time if att.check_out_time else datetime.utcnow()
                meta = compute_check_out_meta(att, calc_time, office, att.employee_id)
                print(f"    Computed Status: {meta.get('status')}")
                print(f"    Computed Working Minutes: {meta.get('working_minutes')}")
                print(f"    Computed Is Half-Day: {meta.get('is_half_day')}")
            except Exception as e:
                print(f"    ERROR: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"    ERROR: No office found!")
    
    print(f"\n{'='*80}\n")
