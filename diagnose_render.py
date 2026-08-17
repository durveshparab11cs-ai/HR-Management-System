#!/usr/bin/env python3
"""
Diagnostic script to test if the app can initialize on Render.
Run this locally to simulate Render environment.
"""

import os
import sys

# Simulate Render environment
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('DATABASE_URL', os.environ.get('DATABASE_URL', 'sqlite:///smart_hrms.db'))

print("=" * 80)
print("DIAGNOSING SMART HRMS RENDER DEPLOYMENT")
print("=" * 80)

# Step 1: Test imports
print("\n[Step 1] Testing imports...")
try:
    from app import create_app
    print("[OK] app.create_app imported successfully")
except Exception as e:
    print(f"[FAIL] Failed to import app.create_app: {e}")
    sys.exit(1)

# Step 2: Create app
print("\n[Step 2] Creating Flask app...")
try:
    app = create_app('production')
    print("[OK] Flask app created successfully")
except Exception as e:
    print(f"[FAIL] Failed to create Flask app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 3: Check database
print("\n[Step 3] Checking database configuration...")
try:
    with app.app_context():
        from app.extensions.database import db
        from sqlalchemy import inspect
        
        engine = db.engine
        print(f"  Database URL: {engine.url}")
        print(f"  Database dialect: {engine.dialect.name}")
        
        # List tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"\n  Tables created ({len(tables)} total):")
        for table in sorted(tables):
            print(f"    - {table}")
        
        # Check critical tables
        critical = ['office_settings', 'employees', 'attendance', 'users']
        missing = [t for t in critical if t not in tables]
        
        if missing:
            print(f"\n  [FAIL] MISSING CRITICAL TABLES: {missing}")
        else:
            print(f"\n  [OK] All critical tables exist")
            
            # Check OfficeSettings data
            print("\n[Step 4] Checking OfficeSettings data...")
            try:
                from app.models.office_settings import OfficeSettings
                office = OfficeSettings.query.first()
                if office:
                    print(f"  [OK] OfficeSettings record found: {office.name}")
                    print(f"    - Location: ({office.latitude}, {office.longitude})")
                    print(f"    - Radius: {office.radius_metres}m")
                else:
                    print(f"  [FAIL] No OfficeSettings record found")
            except Exception as e:
                print(f"  [FAIL] Failed to query OfficeSettings: {e}")
        
except Exception as e:
    print(f"[FAIL] Database check failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 5: Test a request
print("\n[Step 5] Testing a request to /health...")
try:
    with app.test_client() as client:
        response = client.get('/health')
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.get_json()}")
        if response.status_code == 200:
            print("  [OK] Health check passed")
        else:
            print("  [FAIL] Health check failed")
except Exception as e:
    print(f"[FAIL] Request test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("DIAGNOSIS COMPLETE")
print("=" * 80)
