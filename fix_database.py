#!/usr/bin/env python3
"""
Fix database schema issues by creating/updating all tables.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Fix database URL
_db_url = os.environ.get("DATABASE_URL", "")
if _db_url.startswith("postgres://"):
    os.environ["DATABASE_URL"] = _db_url.replace("postgres://", "postgresql://", 1)

from app import create_app
from app.extensions.database import db

print("Initializing database...")
print("")

app = create_app("production")

with app.app_context():
    try:
        print("Creating all database tables...")
        db.create_all()
        print("✓ Database initialized successfully!")
        print("")
        print("Tables created/updated:")
        print("  - Users")
        print("  - Employees")
        print("  - Attendance")
        print("  - Shifts")
        print("  - Leaves")
        print("  - And all other tables")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

print("")
print("✓ Database is ready!")
print("Try logging in again.")
