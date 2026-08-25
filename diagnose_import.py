#!/usr/bin/env python3
"""
Diagnose which app module is being loaded and what coordinator routes exist.
"""

import sys
import os

# Print Python path
print("Python sys.path:")
for p in sys.path[:5]:
    print(f"  {p}")
print()

# Try importing app
print("Attempting to import app...")
try:
    import app
    print(f"✅ app imported from: {app.__file__}")
except ImportError as e:
    print(f"❌ Failed to import app: {e}")
    sys.exit(1)

print()

# Check which coordinator is available
print("Checking app.blueprints.coordinator...")
try:
    from app.blueprints.coordinator import routes
    print(f"✅ coordinator.routes imported from: {routes.__file__}")
    
    # Check what's in routes
    print("\n   Functions in coordinator.routes:")
    for name in dir(routes):
        if not name.startswith('_'):
            obj = getattr(routes, name)
            if callable(obj) and hasattr(obj, '__module__'):
                print(f"      {name}")
    
    # Specifically check for api_search_employee
    if hasattr(routes, 'api_search_employee'):
        print("\n   ✅ api_search_employee found!")
        func = routes.api_search_employee
        print(f"      is_public_api: {getattr(func, 'is_public_api', 'NOT SET')}")
        print(f"      requires_auth: {getattr(func, 'requires_auth', 'NOT SET')}")
    else:
        print("\n   ❌ api_search_employee NOT FOUND")
        print("      Available routes:")
        print("      - dashboard")
        print("      - search_employee")
        print("      - kiosk_checkin")
        print("      - kiosk_checkout")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)
print("CONCLUSION:")
print("=" * 70)

try:
    from app.blueprints.coordinator import routes
    if hasattr(routes, 'api_search_employee'):
        print("✅ New coordinator API is available (smart_hrms version)")
    else:
        print("❌ Old coordinator API is loaded (original /app version)")
        print("   The fix has NOT been deployed to this app instance!")
except:
    print("❌ Cannot determine coordinator version")
