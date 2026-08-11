#!/usr/bin/env python3
"""
Fix missing columns from migration
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import create_app
from app.extensions.database import db
import sqlalchemy as sa

app = create_app()

with app.app_context():
    try:
        print("🔧 Fixing missing columns...")
        
        # Check and add comp_off_work_date to leave_requests
        inspector = sa.inspect(db.engine)
        lr_cols = [col['name'] for col in inspector.get_columns('leave_requests')]
        
        if 'comp_off_work_date' not in lr_cols:
            print("   Adding comp_off_work_date to leave_requests...")
            db.session.execute(sa.text("ALTER TABLE leave_requests ADD COLUMN comp_off_work_date DATE"))
            db.session.commit()
            print("   ✅ comp_off_work_date added")
        else:
            print("   ✅ comp_off_work_date already exists")
        
        # Check and add leave_order to leave_types
        lt_cols = [col['name'] for col in inspector.get_columns('leave_types')]
        
        if 'leave_order' not in lt_cols:
            print("   Adding leave_order to leave_types...")
            db.session.execute(sa.text("ALTER TABLE leave_types ADD COLUMN leave_order INTEGER NOT NULL DEFAULT 0"))
            db.session.commit()
            print("   ✅ leave_order added")
        else:
            print("   ✅ leave_order already exists")
        
        # Verify all columns
        print("\n🔍 Verifying all columns...")
        inspector = sa.inspect(db.engine)
        
        lr_cols = [col['name'] for col in inspector.get_columns('leave_requests')]
        lt_cols = [col['name'] for col in inspector.get_columns('leave_types')]
        
        required_lr = ['comp_off_work_date', 'comp_off_expiry_date', 'comp_off_used_on', 'comp_off_notified']
        required_lt = ['leave_order']
        
        all_ok = True
        for col in required_lr:
            if col in lr_cols:
                print(f"   ✅ leave_requests.{col}")
            else:
                print(f"   ❌ leave_requests.{col}")
                all_ok = False
        
        for col in required_lt:
            if col in lt_cols:
                print(f"   ✅ leave_types.{col}")
            else:
                print(f"   ❌ leave_types.{col}")
                all_ok = False
        
        if all_ok:
            print("\n🎉 All columns verified successfully!")
        else:
            print("\n❌ Some columns still missing")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        db.session.rollback()
