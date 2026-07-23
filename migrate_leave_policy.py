"""
migrate_leave_policy.py
========================
Migrates leave types to new policy:
- Keep only: PL, CL, SL, COMP
- Remove: LOP, ML, PTL, BL
- Update PL: max 6 per year
- Update CL, SL, COMP: unlimited (999)

Run: python migrate_leave_policy.py
"""
import os
import sys
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
    print("=== Leave Policy Migration ===\n")
    
    # Remove unwanted leave types
    removed_codes = ["LOP", "ML", "PTL", "BL"]
    for code in removed_codes:
        lt = LeaveType.query.filter_by(code=code).first()
        if lt:
            print(f"❌ Removing: {lt.name} ({lt.code})")
            db.session.delete(lt)
    
    # Update/Create required leave types
    required = [
        {"name": "Paid Leave",   "code": "PL",   "max_days_per_year": 6,   "is_paid": True, "color": "#10b981", "description": "Maximum 6 per year, one per 2-month period"},
        {"name": "Casual Leave", "code": "CL",   "max_days_per_year": 999, "is_paid": True, "color": "#3b82f6", "description": "Unlimited"},
        {"name": "Sick Leave",   "code": "SL",   "max_days_per_year": 999, "is_paid": True, "color": "#ef4444", "description": "Unlimited", "requires_document": True},
        {"name": "Comp Off",     "code": "COMP", "max_days_per_year": 999, "is_paid": True, "color": "#8b5cf6", "description": "Unlimited"},
    ]
    
    for lt_data in required:
        lt = LeaveType.query.filter_by(code=lt_data["code"]).first()
        if lt:
            # Update existing
            lt.max_days_per_year = lt_data["max_days_per_year"]
            lt.description = lt_data.get("description", "")
            lt.is_active = True
            print(f"✅ Updated: {lt.name} ({lt.code}) → {lt.max_days_per_year} days/year")
        else:
            # Create new
            lt = LeaveType(**lt_data)
            db.session.add(lt)
            print(f"➕ Created: {lt_data['name']} ({lt_data['code']})")
    
    db.session.commit()
    
    print("\n=== Final Leave Types ===")
    for lt in LeaveType.query.filter_by(is_active=True).order_by(LeaveType.id).all():
        status = "Unlimited" if lt.max_days_per_year >= 999 else f"{lt.max_days_per_year} days/year"
        print(f"  [{lt.id}] {lt.code:5} — {lt.name:20} | {status}")
    
    print("\n✅ Migration complete!")
