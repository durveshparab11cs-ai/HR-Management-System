#!/usr/bin/env python
"""
ensure_comp_off_leavetype.py
============================
EMERGENCY SCRIPT: Ensures Comp Off leave type exists in production database.

Run this FIRST thing after deploying to Render to guarantee the CO leave type is created.
This is a failsafe to prevent the missing CO card issue.

Usage:
    python ensure_comp_off_leavetype.py
"""

import os
import sys
from datetime import datetime

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("=" * 70)
    print("COMP OFF LEAVE TYPE INITIALIZATION")
    print("=" * 70)
    print()
    
    try:
        # Import app and create context
        from app import create_app
        from app.extensions.database import db
        from app.models.leave import LeaveType
        
        app = create_app(os.getenv("FLASK_ENV", "production"))
        
        with app.app_context():
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Connecting to database...")
            
            # Check if CO leave type exists
            co_type = LeaveType.query.filter_by(code='CO').first()
            
            if co_type:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ CO leave type exists: {co_type.name}")
                print(f"                      ID={co_type.id}, is_active={co_type.is_active}, color={co_type.color}")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  CO leave type NOT FOUND. Creating...")
                
                # Create CO leave type
                co = LeaveType(
                    code='CO',
                    name='Comp Off',
                    max_days_per_year=6,
                    is_paid=True,
                    requires_document=False,
                    color='#8b5cf6',  # Purple
                    is_active=True,
                )
                db.session.add(co)
                db.session.commit()
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Created CO leave type: ID={co.id}, name={co.name}")
            
            # Also verify all 4 required leave types
            print()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Verifying all 4 required leave types...")
            required_types = ['CL', 'SL', 'PL', 'CO']
            
            for code in required_types:
                lt = LeaveType.query.filter_by(code=code).first()
                if lt:
                    status = "✅" if lt.is_active else "⚠️  (inactive)"
                    print(f"  {status} {code:3} | {lt.name:20} | active={lt.is_active}")
                else:
                    print(f"  ❌ {code:3} | NOT FOUND")
            
            print()
            print("=" * 70)
            print("✅ COMP OFF LEAVE TYPE INITIALIZATION COMPLETE")
            print("=" * 70)
            return 0
    
    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ ERROR: {str(e)}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
