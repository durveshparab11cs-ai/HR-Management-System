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
        {"name": "Casual Leave",      "code": "CL",   "max_days_per_year": 12, "is_paid": True,  "color": "#3b82f6"},
        {"name": "Sick Leave",        "code": "SL",   "max_days_per_year": 12, "is_paid": True,  "color": "#ef4444", "requires_document": True},
        {"name": "Paid Leave",        "code": "PL",   "max_days_per_year": 15, "is_paid": True,  "color": "#10b981"},
        {"name": "Loss of Pay",       "code": "LOP",  "max_days_per_year": 30, "is_paid": False, "color": "#f59e0b"},
        {"name": "Comp Off",          "code": "COMP", "max_days_per_year": 6,  "is_paid": True,  "color": "#8b5cf6"},
        {"name": "Maternity Leave",   "code": "ML",   "max_days_per_year": 180,"is_paid": True,  "color": "#ec4899"},
        {"name": "Paternity Leave",   "code": "PTL",  "max_days_per_year": 15, "is_paid": True,  "color": "#0891b2"},
        {"name": "Bereavement Leave", "code": "BL",   "max_days_per_year": 5,  "is_paid": True,  "color": "#6b7280"},
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
