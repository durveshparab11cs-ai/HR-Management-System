"""
update_half_day_threshold.py
==============================
Update half_day_threshold from 240 (4 hours) to 300 (5 hours) in database.

USAGE:
    python update_half_day_threshold.py

This updates the existing office_settings record(s) in the database.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app import create_app
from app.extensions.database import db
from app.models.office_settings import OfficeSettings


def update_threshold():
    """Update half_day_threshold to 300 minutes (5 hours)."""
    app = create_app()
    
    with app.app_context():
        print("=" * 70)
        print("UPDATING HALF-DAY THRESHOLD")
        print("=" * 70)
        print()
        
        # Get all office settings
        offices = OfficeSettings.query.all()
        
        if not offices:
            print("⚠️  No office settings found in database.")
            print("   The default (300 minutes) will be used for new records.")
            return
        
        print(f"📊 Found {len(offices)} office setting(s)")
        print()
        
        updated_count = 0
        for office in offices:
            old_threshold = office.half_day_threshold_minutes
            
            if old_threshold == 240:
                office.half_day_threshold_minutes = 300
                db.session.add(office)
                updated_count += 1
                print(f"✅ Updated '{office.name}': 240 min (4h) → 300 min (5h)")
            elif old_threshold == 300:
                print(f"ℹ️  '{office.name}': Already set to 300 min (5h)")
            else:
                print(f"⚠️  '{office.name}': Custom value {old_threshold} min - not changed")
        
        if updated_count > 0:
            db.session.commit()
            print()
            print(f"✅ Updated {updated_count} office setting(s)")
        else:
            print()
            print("ℹ️  No updates needed")
        
        print()
        print("=" * 70)
        print("VERIFICATION")
        print("=" * 70)
        print()
        
        for office in OfficeSettings.query.all():
            print(f"Office: {office.name}")
            print(f"  Half-day threshold: {office.half_day_threshold_minutes} minutes ({office.half_day_threshold_minutes / 60:.1f} hours)")
            print()
        
        print("=" * 70)
        print("✅ HALF-DAY THRESHOLD UPDATE COMPLETE!")
        print("=" * 70)
        print()
        print("Employees now need to work 5 hours for full day.")
        print("Working less than 5 hours = Half day")
        print()


if __name__ == "__main__":
    update_threshold()
