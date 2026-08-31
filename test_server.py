#!/usr/bin/env python
import os
import sys

# Force SQLite
os.environ["DATABASE_URL"] = "sqlite:///smart_hrms_dev.db"
os.environ["FLASK_ENV"] = "development"

print("Attempting to create app...")
try:
    from app import create_app
    print("✓ App module imported")
    
    app = create_app("development")
    print("✓ App created successfully!")
    
    # List coordinator routes
    print("\nCoordinator routes:")
    for rule in app.url_map.iter_rules():
        if 'coordinator' in rule.rule:
            print(f"  {rule.rule}")
    
    # Quick test
    with app.test_client() as client:
        print("\nTesting /coordinator/portal...")
        resp = client.get('/coordinator/portal')
        print(f"  Status: {resp.status_code}")
        if resp.status_code == 200:
            print("  ✓ Portal OK (first 100 chars of HTML)")
            print(f"  {resp.data[:100]}")
except Exception as e:
    print(f"✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
