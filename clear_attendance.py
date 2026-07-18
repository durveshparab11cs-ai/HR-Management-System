"""
clear_attendance.py
====================
One-time script to clear all attendance data for a fresh start.
Run from Render Shell:
    python clear_attendance.py

Deletes (in order to respect FK constraints):
    1. attendance_photos
    2. attendance_logs
    3. gps_logs
    4. attendance
"""

import os
import sys

# Bootstrap Flask app
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("FLASK_ENV", "production")

from app import create_app
from app.extensions.database import db

app = create_app("production")

with app.app_context():
    try:
        from sqlalchemy import text

        # Count before
        att_count   = db.session.execute(text("SELECT COUNT(*) FROM attendance")).scalar()
        photo_count = db.session.execute(text("SELECT COUNT(*) FROM attendance_photos")).scalar()
        log_count   = db.session.execute(text("SELECT COUNT(*) FROM attendance_logs")).scalar() if _table_exists(db, "attendance_logs") else 0
        gps_count   = db.session.execute(text("SELECT COUNT(*) FROM gps_logs")).scalar() if _table_exists(db, "gps_logs") else 0

        print(f"Before: attendance={att_count}, photos={photo_count}, logs={log_count}, gps={gps_count}")

        confirm = input("Type YES to delete all attendance records: ").strip()
        if confirm != "YES":
            print("Aborted.")
            sys.exit(0)

        # Delete in FK order
        if _table_exists(db, "attendance_photos"):
            db.session.execute(text("DELETE FROM attendance_photos"))
            print("  ✓ Cleared attendance_photos")

        if _table_exists(db, "gps_logs"):
            db.session.execute(text("DELETE FROM gps_logs"))
            print("  ✓ Cleared gps_logs")

        if _table_exists(db, "attendance_logs"):
            db.session.execute(text("DELETE FROM attendance_logs"))
            print("  ✓ Cleared attendance_logs")

        db.session.execute(text("DELETE FROM attendance"))
        print("  ✓ Cleared attendance")

        db.session.commit()
        print("\nDone. All attendance records cleared. You can now check in fresh.")

    except Exception as exc:
        db.session.rollback()
        print(f"Error: {exc}")
        sys.exit(1)


def _table_exists(db, table_name):
    from sqlalchemy import inspect
    insp = inspect(db.engine)
    return table_name in insp.get_table_names()
