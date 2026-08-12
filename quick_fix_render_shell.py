#!/usr/bin/env python
"""
quick_fix_render_shell.py
==========================
RUN THIS IN RENDER WEB SERVICE SHELL (if you have access)

This script will:
1. Connect to the production database
2. Ensure the CO leave type exists with code='CO' (not 'COMP')
3. Verify all 4 required leave types are present
4. Print results

COPY-PASTE COMMAND FOR RENDER SHELL:
    python quick_fix_render_shell.py
"""

import os
import sys
from datetime import datetime

# CONFIGURATION - should match Render's environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///instance/smart_hrms_dev.db")

print("=" * 70)
print("PRODUCTION DATABASE FIXER")
print("=" * 70)
print(f"Database URL: {DATABASE_URL[:50]}...")
print()

try:
    # This import structure works in Render shell after install
    from app import create_app
    from app.extensions.database import db
    from app.models.leave import LeaveType
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Loading Flask app...")
    app = create_app("production")
    
    with app.app_context():
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking leave types...")
        
        # Check current state
        all_types = LeaveType.query.all()
        print(f"Total leave types in DB: {len(all_types)}")
        
        for lt in all_types:
            print(f"  - {lt.code:5} | {lt.name:20} | active={lt.is_active} | id={lt.id}")
        
        print()
        
        # Fix CRITICAL: Ensure CO exists
        co_type = LeaveType.query.filter_by(code='CO').first()
        comp_type = LeaveType.query.filter_by(code='COMP').first()
        
        if co_type:
            print(f"✅ CO leave type exists: {co_type.name} (id={co_type.id})")
        else:
            print(f"❌ CO leave type NOT found. Creating...")
            co_new = LeaveType(
                code='CO',
                name='Comp Off',
                max_days_per_year=6,
                is_paid=True,
                color='#8b5cf6',
                is_active=True,
            )
            db.session.add(co_new)
            db.session.commit()
            print(f"✅ Created CO: id={co_new.id}")
        
        # If COMP exists but CO doesn't, update COMP's code to CO
        if comp_type and not co_type:
            print(f"⚠️  Found old COMP code, upgrading to CO...")
            comp_type.code = 'CO'
            db.session.commit()
            print(f"✅ Upgraded COMP (id={comp_type.id}) → CO")
        
        # Verify all required types
        print()
        print("Final State:")
        required = ['CL', 'SL', 'PL', 'CO']
        for code in required:
            lt = LeaveType.query.filter_by(code=code).first()
            if lt:
                print(f"  ✅ {code} | {lt.name}")
            else:
                print(f"  ❌ {code} | MISSING")
        
        print()
        print("=" * 70)
        print("✅ COMPLETE - Database is ready for Comp Off card display")
        print("=" * 70)

except ImportError as ie:
    print(f"❌ Import error: {ie}")
    print("Make sure you're running this from within the Render shell environment")
    print("or from the workspace root with dependencies installed.")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
