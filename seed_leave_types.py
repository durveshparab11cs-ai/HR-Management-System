"""
seed_leave_types.py
====================
Seeds leave types into the database.
Run on Render Shell: python seed_leave_types.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("FLASK_ENV", "production")

from dotenv import load_dotenv
load_dotenv()

_db_url = os.environ.get("DATABASE_URL", "")
if _db_url.startswith("postgres://"):
    os.environ["DATABASE_URL"] = _db_url.replace("postgres://", "postgresql://", 1)

from app import create_app
from app.extensions.database import db
from app.models.leave import LeaveType

app = create_app("production")

with app.app_context():
    db.create_all()

    leave_types = [
        {"name": "Paid Leave",   "code": "PL",   "max_days_per_year": 6,  "is_paid": True,  "color": "#10b981", "description": "Maximum 6 per year, one per 2-month period"},
        {"name": "Casual Leave", "code": "CL",   "max_days_per_year": 999,"is_paid": True,  "color": "#3b82f6", "description": "Unlimited"},
        {"name": "Sick Leave",   "code": "SL",   "max_days_per_year": 999,"is_paid": True,  "color": "#ef4444", "description": "Unlimited", "requires_document": True},
        {"name": "Comp Off",     "code": "COMP", "max_days_per_year": 999,"is_paid": True,  "color": "#8b5cf6", "description": "Unlimited"},
    ]

    added = 0
    for lt_data in leave_types:
        if not LeaveType.query.filter_by(code=lt_data["code"]).first():
            db.session.add(LeaveType(**lt_data))
            added += 1

    db.session.commit()
    total = LeaveType.query.count()
    print(f"Added {added} leave types. Total in DB: {total}")
    for lt in LeaveType.query.order_by(LeaveType.id).all():
        print(f"  [{lt.id}] {lt.code} — {lt.name}")
