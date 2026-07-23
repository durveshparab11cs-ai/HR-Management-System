"""
reset_attendance.py
====================
Complete attendance data reset for development/testing.

USAGE:
    python reset_attendance.py

WHAT IT DOES:
    1. Deletes ALL attendance records
    2. Deletes ALL attendance photos (DB records)
    3. Deletes ALL attendance logs (GPS logs, audit logs)
    4. Deletes orphaned photo files from uploads folder
    5. Preserves: employees, departments, leaves, payroll, users, office settings

SAFETY:
    - Asks for confirmation before deletion
    - Shows count of records to be deleted
    - Cannot be undone!
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app
from app.extensions.database import db
from app.models.attendance import Attendance
from app.models.attendance_photo import AttendancePhoto
from app.models.attendance_log import AttendanceLog


def reset_attendance():
    """Complete attendance database reset."""
    app = create_app()
    
    with app.app_context():
        print("=" * 70)
        print("ATTENDANCE MODULE RESET")
        print("=" * 70)
        print()
        
        # Count records
        attendance_count = Attendance.query.count()
        photo_count = AttendancePhoto.query.count()
        log_count = AttendanceLog.query.count()
        
        print(f"📊 Current Records:")
        print(f"   - Attendance records: {attendance_count}")
        print(f"   - Attendance photos: {photo_count}")
        print(f"   - Attendance logs: {log_count}")
        print()
        
        if attendance_count == 0 and photo_count == 0 and log_count == 0:
            print("✅ Attendance database is already empty!")
            return
        
        print("⚠️  WARNING: This will permanently delete ALL attendance data!")
        print("   - All check-in and check-out records")
        print("   - All attendance history")
        print("   - All proof photos (DB and files)")
        print("   - All GPS logs")
        print("   - All audit logs")
        print()
        print("   This WILL NOT delete:")
        print("   - Employees")
        print("   - Departments")
        print("   - Leave records")
        print("   - Payroll")
        print("   - Users")
        print("   - Office settings")
        print()
        
        response = input("Type 'DELETE ALL' to confirm: ")
        
        if response != "DELETE ALL":
            print("❌ Cancelled. No changes made.")
            return
        
        print()
        print("🗑️  Deleting records...")
        print()
        
        try:
            # 1. Delete attendance logs
            if log_count > 0:
                print(f"   Deleting {log_count} attendance logs...")
                AttendanceLog.query.delete()
                db.session.commit()
                print(f"   ✅ Deleted {log_count} logs")
            
            # 2. Delete attendance photos
            if photo_count > 0:
                print(f"   Deleting {photo_count} attendance photos...")
                AttendancePhoto.query.delete()
                db.session.commit()
                print(f"   ✅ Deleted {photo_count} photos")
            
            # 3. Delete attendance records
            if attendance_count > 0:
                print(f"   Deleting {attendance_count} attendance records...")
                Attendance.query.delete()
                db.session.commit()
                print(f"   ✅ Deleted {attendance_count} attendance records")
            
            # 4. Clean up orphaned photo files
            print()
            print("🧹 Cleaning up orphaned photo files...")
            upload_folder = Path(app.config.get("UPLOAD_FOLDER", "./instance/uploads"))
            if not upload_folder.is_absolute():
                upload_folder = Path(app.root_path).parent / str(upload_folder).lstrip("./")
            
            attendance_folder = upload_folder / "attendance"
            if attendance_folder.exists():
                deleted_files = 0
                for file_path in attendance_folder.rglob("*"):
                    if file_path.is_file():
                        file_path.unlink()
                        deleted_files += 1
                print(f"   ✅ Deleted {deleted_files} orphaned photo files")
            else:
                print(f"   ℹ️  No attendance uploads folder found")
            
            print()
            print("=" * 70)
            print("✅ ATTENDANCE RESET COMPLETE!")
            print("=" * 70)
            print()
            print("Verification:")
            print(f"   - Attendance records: {Attendance.query.count()}")
            print(f"   - Attendance photos: {AttendancePhoto.query.count()}")
            print(f"   - Attendance logs: {AttendanceLog.query.count()}")
            print()
            
        except Exception as exc:
            db.session.rollback()
            print()
            print(f"❌ ERROR: {exc}")
            print()
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    reset_attendance()
