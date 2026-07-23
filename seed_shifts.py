"""Seed default shifts for testing"""
import datetime
from app import create_app
from app.extensions.database import db
from app.models.company import Shift

app = create_app()

with app.app_context():
    print("=" * 70)
    print("SEEDING DEFAULT SHIFTS")
    print("=" * 70)
    print()
    
    # Check existing shifts
    existing = Shift.query.all()
    if existing:
        print(f"Found {len(existing)} existing shifts:")
        for s in existing:
            print(f"  - {s.name} ({s.code}): {s.start_time} - {s.end_time}")
        print()
        response = input("Delete existing shifts and reseed? (y/n): ")
        if response.lower() == 'y':
            for s in existing:
                db.session.delete(s)
            db.session.commit()
            print("Deleted existing shifts")
        else:
            print("Keeping existing shifts")
            exit(0)
    
    # Create default shifts
    shifts_data = [
        {
            "name": "Morning Shift",
            "code": "MORNING",
            "start_time": datetime.time(9, 0),
            "end_time": datetime.time(18, 0),
            "grace_minutes": 15,
            "break_minutes": 60,
            "working_days": "Mon-Fri",
            "is_night_shift": False,
            "is_active": True,
            "description": "Standard morning shift 9 AM to 6 PM"
        },
        {
            "name": "Evening Shift",
            "code": "EVENING",
            "start_time": datetime.time(14, 0),
            "end_time": datetime.time(23, 0),
            "grace_minutes": 15,
            "break_minutes": 60,
            "working_days": "Mon-Fri",
            "is_night_shift": False,
            "is_active": True,
            "description": "Evening shift 2 PM to 11 PM"
        },
        {
            "name": "Night Shift",
            "code": "NIGHT",
            "start_time": datetime.time(22, 0),
            "end_time": datetime.time(6, 0),
            "grace_minutes": 15,
            "break_minutes": 60,
            "working_days": "Mon-Fri",
            "is_night_shift": True,
            "is_active": True,
            "description": "Night shift 10 PM to 6 AM"
        },
        {
            "name": "Flexible Shift",
            "code": "FLEXIBLE",
            "start_time": datetime.time(10, 0),
            "end_time": datetime.time(19, 0),
            "grace_minutes": 30,
            "break_minutes": 60,
            "working_days": "Mon-Fri",
            "is_night_shift": False,
            "is_active": True,
            "description": "Flexible shift 10 AM to 7 PM with 30 min grace"
        },
    ]
    
    print(f"Creating {len(shifts_data)} default shifts...")
    print()
    
    for shift_data in shifts_data:
        shift = Shift(**shift_data)
        db.session.add(shift)
        print(f"✅ Created: {shift.name} ({shift.code})")
        print(f"   Time: {shift.start_time.strftime('%I:%M %p')} - {shift.end_time.strftime('%I:%M %p')}")
        print(f"   Working hours: {shift.working_hours}h per day")
        print()
    
    db.session.commit()
    
    print("=" * 70)
    print("✅ SEEDING COMPLETE!")
    print("=" * 70)
    print()
    print(f"Total shifts in database: {Shift.query.count()}")
