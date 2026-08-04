#!/usr/bin/env python
"""Check for duplicate photos causing duplicate rows."""

from app import create_app
from app.models.attendance import Attendance
from app.models.attendance_photo import AttendancePhoto
from datetime import date, timedelta

app = create_app()

with app.app_context():
    # Get all attendance + photo records from last 10 days
    start_date = date.today() - timedelta(days=10)
    
    records = Attendance.query.filter(
        Attendance.date >= start_date,
        Attendance.is_deleted == False
    ).order_by(Attendance.date.desc()).all()
    
    print(f"Total attendance records: {len(records)}\n")
    
    # Check photos per attendance
    for att in records[:10]:  # Show first 10
        photos = AttendancePhoto.query.filter_by(attendance_id=att.id).all()
        print(f"Date: {att.date}, Employee: {att.employee_id}, Attendance ID: {att.id}")
        print(f"  Status: {att.status}, Photos: {len(photos)}")
        for photo in photos:
            print(f"    - Photo ID: {photo.id}, has_image: {bool(photo.image_data)}, has_file: {bool(photo.file_path)}")
        print()

print("Done")
