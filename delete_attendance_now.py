"""
delete_attendance_now.py
=========================
IMMEDIATELY delete all attendance data - no confirmation needed.
"""

from app import create_app
from app.extensions.database import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("=" * 70)
    print("DELETING ALL ATTENDANCE DATA")
    print("=" * 70)
    
    try:
        # Delete in order to respect foreign keys
        tables = [
            "gps_logs",
            "attendance_photos", 
            "attendance_logs",
            "attendance"
        ]
        
        total_deleted = 0
        
        for table in tables:
            try:
                # Count before
                count = db.session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                
                if count > 0:
                    # Delete all
                    db.session.execute(text(f"DELETE FROM {table}"))
                    # Reset sequence
                    db.session.execute(text(f"DELETE FROM sqlite_sequence WHERE name='{table}'"))
                    print(f"✅ {table}: {count} records deleted")
                    total_deleted += count
                else:
                    print(f"ℹ️  {table}: Already empty")
                    
            except Exception as e:
                print(f"⚠️  {table}: {str(e)}")
        
        # Commit
        db.session.commit()
        
        print()
        print("=" * 70)
        print(f"✅ DELETED {total_deleted} ATTENDANCE RECORDS")
        print("=" * 70)
        print()
        print("All attendance data has been removed!")
        print("Employees can now start fresh.")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERROR: {str(e)}")
